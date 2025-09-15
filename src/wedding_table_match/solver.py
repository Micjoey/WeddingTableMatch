# /Users/macallansavett/code/WeddingTableMatch/src/wedding_table_match/solver.py
"""
Relationship aware seating solver.

Relationship scale for table grading:
    best friend: +5
    friend: +3
    know: +2
    neutral: 0
    avoid: -3
    conflict: -5
Table compatibility is graded A to F based on the average relationship score among all pairs at the table.
"""
from __future__ import annotations

from itertools import combinations
from typing import Callable, Dict, List, Set, Tuple

from .models import Guest, Table, Relationship


# ----------------------------- scoring helpers -----------------------------
_RELATION_VALUE = {
    "best friend": 5,
    "friend": 3,
    "know": 2,
    "neutral": 0,        # neutral should not inflate scores
    "avoid": -3,
    "conflict": -5,
}


def relation_value(rel: Relationship) -> int:
    return _RELATION_VALUE.get(rel.relation, rel.strength)


def compute_table_stats(members: List[str], get_rel: Callable[[str, str], Relationship]) -> Dict[str, int | float]:
    """Compute total and mean pair scores plus sign breakdown for a set of members."""
    total = 0
    pos = neg = neu = 0
    pairs = 0
    for a, b in combinations(members, 2):
        v = relation_value(get_rel(a, b))
        total += v
        pairs += 1
        if v > 0:
            pos += 1
        elif v < 0:
            neg += 1
        else:
            neu += 1
    mean = total / pairs if pairs else 0.0
    return {
        "total_score": total,
        "mean_score": mean,
        "pair_count": pairs,
        "pos_pairs": pos,
        "neg_pairs": neg,
        "neu_pairs": neu,
    }


def grade_tables(stats: List[Dict[str, int | float]]) -> List[Dict[str, int | float | str]]:
    """Assign A to F based on mean score thresholds."""
    graded = []
    for s in stats:
        m = s["mean_score"]
        if m >= 2.5:
            g = "A"
        elif m >= 1.5:
            g = "B"
        elif m >= 0.8:
            g = "C"
        elif m >= 0.2:
            g = "D"
        else:
            g = "F"
        out = dict(s)
        out["grade"] = g
        graded.append(out)
    return graded


# ----------------------------- model -----------------------------
class SeatingModel:
    """Greedy plus beam search seating solver with relationship awareness."""

    def __init__(
        self,
        maximize_known: bool = False,
        group_singles: bool = False,
        min_known: int = 0,
        min_unknown: int = 0,
        max_unknown: int = 3,
        group_by_meal_preference: bool = False,
    ) -> None:
        # Inputs
        self.guests: List[Guest] = []
        self.tables: List[Table] = []
        self.relationships: Dict[Tuple[str, str], Relationship] = {}
        # Hard constraints
        self.must_separate: Dict[str, Set[str]] = {}
        # Soft preferences
        self.maximize_known = maximize_known
        self.group_singles = group_singles
        self.min_known = min_known
        self.min_unknown = min_unknown
        self.max_unknown = max_unknown
        self.group_by_meal_preference = group_by_meal_preference
        # Id mapping helpers
        self.id_by_name: Dict[str, str] = {}
        self.name_by_id: Dict[str, str] = {}

    def build(
        self, guests: List[Guest], tables: List[Table], relationships: List[Relationship]
    ) -> None:
        """Store model data."""
        self.guests = guests
        self.tables = tables
        self.id_by_name = {g.name: g.id for g in guests}
        self.name_by_id = {g.id: g.name for g in guests}

        # Index relationships by both ids and names for robustness.
        self.relationships = {}
        for r in relationships:
            a_variants = {r.a}
            b_variants = {r.b}
            if r.a in self.name_by_id:
                a_variants.add(self.name_by_id[r.a])
            if r.a in self.id_by_name:
                a_variants.add(self.id_by_name[r.a])
            if r.b in self.name_by_id:
                b_variants.add(self.name_by_id[r.b])
            if r.b in self.id_by_name:
                b_variants.add(self.id_by_name[r.b])
            for a_key in a_variants:
                for b_key in b_variants:
                    rr = Relationship(a=a_key, b=b_key, relation=r.relation, strength=r.strength, notes=r.notes)
                    self.relationships[(a_key, b_key)] = rr
                    self.relationships[(b_key, a_key)] = Relationship(a=b_key, b=a_key, relation=r.relation, strength=r.strength, notes=r.notes)

        # Build symmetric must_separate map
        self.must_separate = {g.name: set(g.must_separate) for g in guests}
        for g in guests:
            for other in g.must_separate:
                self.must_separate.setdefault(other, set()).add(g.name)

    def get_relationship(self, a: str, b: str) -> Relationship:
        """Return relationship for a pair. Defaults to neutral when unknown."""
        return self.relationships.get((a, b)) or Relationship(a=a, b=b, relation="neutral", strength=0, notes="")

    # ----------------------------- internals -----------------------------
    def _build_groups(self) -> List[List[str]]:
        """Union guests chained by must_with."""
        parent: Dict[str, str] = {g.name: g.name for g in self.guests}

        def find(x: str) -> str:
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        def union(a: str, b: str) -> None:
            pa, pb = find(a), find(b)
            if pa != pb:
                parent[pa] = pb

        for g in self.guests:
            for other in g.must_with:
                union(g.name, other)

        groups: Dict[str, List[str]] = {}
        for name in parent:
            root = find(name)
            groups.setdefault(root, []).append(name)

        return sorted([sorted(members) for members in groups.values()], key=lambda g: (-len(g), g[0]))

    def _feasible_with(self, group: List[str], table_name: str, assignments: Dict[str, str], table_slots: Dict[str, int]) -> bool:
        """Hard checks only: capacity, must_separate, avoid."""
        if table_slots[table_name] < len(group):
            return False
        existing = [name for name, t in assignments.items() if t == table_name]
        combined = existing + group
        for a, b in combinations(combined, 2):
            if b in self.must_separate.get(a, set()):
                return False
            rel = self.get_relationship(a, b)
            if rel.relation == "avoid":
                return False
        return True

    def _count_known_unknown(self, member: str, combined: List[str]) -> tuple[int, int, int]:
        """Return counts for a given member: (known, neutral, negative)."""
        known = neutral = negative = 0
        for other in combined:
            if other == member:
                continue
            v = relation_value(self.get_relationship(member, other))
            if v > 0:
                known += 1
            elif v < 0:
                negative += 1
            else:
                neutral += 1
        return known, neutral, negative

    def _table_delta(self, group: List[str], table_name: str, assignments: Dict[str, str], table_slots: Dict[str, int]) -> int:
        """Return the change in total score if we seat group at table_name.

        Components:
        - Pair score delta using categorical values.
        - Soft bonus if member meets min_known.
        - Soft bonus if member's neutral count lies within [min_unknown, max_unknown].
          Penalty if outside. Per guest CSV min_unknown overrides global.
        """
        existing = [name for name, t in assignments.items() if t == table_name]
        combined = existing + group

        # Old and new pair totals
        old_total = compute_table_stats(existing, self.get_relationship)["total_score"] if len(existing) >= 2 else 0
        new_total = compute_table_stats(combined, self.get_relationship)["total_score"]
        delta = int(new_total - old_total)

        # Soft per guest bonuses and penalties
        bonus = 0
        for member in group:
            # Per guest overrides if provided
            guest_obj = next((g for g in self.guests if g.name == member), None)
            g_min_known = self.min_known
            g_min_unknown = self.min_unknown
            g_max_unknown = self.max_unknown
            if guest_obj:
                if getattr(guest_obj, "min_known", 0) > 0:
                    g_min_known = guest_obj.min_known
                # Guest model has min_unknown. No max_unknown field in model, so use global for now.
                if getattr(guest_obj, "min_unknown", 0) > 0:
                    g_min_unknown = guest_obj.min_unknown

            known, neutral, negative = self._count_known_unknown(member, combined)

            # Known preference
            if g_min_known > 0 and known >= g_min_known:
                bonus += 8  # tuned small to avoid overpowering pair scores

            # Unknown window preference
            if g_min_unknown == 0 and g_max_unknown == 0:
                pass
            else:
                if g_min_unknown <= neutral <= g_max_unknown:
                    bonus += 6
                else:
                    # Penalize distance from window edges
                    if neutral < g_min_unknown:
                        bonus -= 3 * (g_min_unknown - neutral)
                    if neutral > g_max_unknown:
                        bonus -= 2 * (neutral - g_max_unknown)

            # Light penalty for too many negatives around a member
            if negative >= 1:
                bonus -= 5 * negative

        return delta + bonus

    def _optimize_assignments(self, assignments: Dict[str, str], table_slots: Dict[str, int]) -> Dict[str, str]:
        """Local pair swap hill climb that respects hard constraints."""
        improved = True
        iters = 0
        while improved and iters < 10:
            improved = False
            iters += 1
            guest_list = list(assignments.keys())
            for i in range(len(guest_list)):
                for j in range(i + 1, len(guest_list)):
                    g1, g2 = guest_list[i], guest_list[j]
                    t1, t2 = assignments[g1], assignments[g2]
                    if t1 == t2:
                        continue
                    new_assign = dict(assignments)
                    new_assign[g1], new_assign[g2] = t2, t1
                    # Feasibility at both tables
                    group1 = [n for n, t in new_assign.items() if t == t1]
                    group2 = [n for n, t in new_assign.items() if t == t2]
                    if not self._feasible_with(group1, t1, {k: v for k, v in new_assign.items() if v == t1}, {t1: len(group1)}):
                        continue
                    if not self._feasible_with(group2, t2, {k: v for k, v in new_assign.items() if v == t2}, {t2: len(group2)}):
                        continue
                    # Score improvement
                    old1 = compute_table_stats([n for n, t in assignments.items() if t == t1], self.get_relationship)["total_score"]
                    old2 = compute_table_stats([n for n, t in assignments.items() if t == t2], self.get_relationship)["total_score"]
                    new1 = compute_table_stats(group1, self.get_relationship)["total_score"]
                    new2 = compute_table_stats(group2, self.get_relationship)["total_score"]
                    if new1 + new2 > old1 + old2:
                        assignments = new_assign
                        improved = True
        return assignments

    # ----------------------------- main solve -----------------------------
    def solve(self) -> Dict[str, str]:
        """Assign guests to tables using beam search with greedy fallback."""
        groups = self._build_groups()

        # Optional regrouping: by meal
        if self.group_by_meal_preference:
            by_meal: Dict[str, List[str]] = {}
            for g in groups:
                for name in g:
                    guest = next((guest for guest in self.guests if guest.name == name), None)
                    meal = getattr(guest, "meal_preference", "") if guest else ""
                    by_meal.setdefault(meal, []).append(name)
            groups = [sorted(members) for members in by_meal.values() if members]

        # Optional regrouping: singles
        if self.group_singles:
            singles = [g for g in self.guests if getattr(g, "single", False) and not getattr(g, "plus_one", False)]
            singles_names = {g.name for g in singles}
            non_single_groups = [g for g in groups if not any(n in singles_names for n in g)]
            s = sorted(list(singles_names))
            singles_groups = [s[i:i + 3] for i in range(0, len(s), 3)]
            groups = non_single_groups + singles_groups

        # Split groups that exceed any table capacity
        if self.tables:
            max_size = max(t.capacity for t in self.tables)
            split = []
            for g in groups:
                if len(g) > max_size:
                    for i in range(0, len(g), max_size):
                        split.append(g[i:i + max_size])
                else:
                    split.append(g)
            groups = split

        # Beam search
        from heapq import nlargest

        initial_slots = {t.name: t.capacity for t in self.tables}
        beam: List[Tuple[Dict[str, str], Dict[str, int], int]] = [({}, initial_slots, 0)]
        beam_width = 5

        for group in groups:
            next_beam: List[Tuple[Dict[str, str], Dict[str, int], int]] = []
            for assignments, table_slots, cum_score in beam:
                candidates: List[Tuple[str, int]] = []
                for table in self.tables:
                    if not self._feasible_with(group, table.name, assignments, table_slots):
                        continue
                    delta = self._table_delta(group, table.name, assignments, table_slots)
                    candidates.append((table.name, delta))
                if not candidates:
                    continue
                candidates.sort(key=lambda x: x[1], reverse=True)
                for table_name, delta in candidates[:beam_width]:
                    new_assign = dict(assignments)
                    new_slots = dict(table_slots)
                    for member in group:
                        new_assign[member] = table_name
                        new_slots[table_name] -= 1
                    next_beam.append((new_assign, new_slots, cum_score + delta))
            if not next_beam:
                break
            beam = nlargest(beam_width, next_beam, key=lambda s: s[2])

        if beam:
            best_assign, best_slots, _ = max(beam, key=lambda s: s[2])
            best_assign = self._optimize_assignments(best_assign, best_slots)
            return best_assign

        # Fallback greedy if beam fails
        assignments: Dict[str, str] = {}
        table_slots = {t.name: t.capacity for t in self.tables}
        for group in groups:
            best_table = None
            best_delta = None
            for table in self.tables:
                if not self._feasible_with(group, table.name, assignments, table_slots):
                    continue
                delta = self._table_delta(group, table.name, assignments, table_slots)
                if best_delta is None or delta > best_delta:
                    best_delta = delta
                    best_table = table.name
            if best_table is None:
                raise ValueError(f"No valid table for group: {', '.join(group)}")
            for member in group:
                assignments[member] = best_table
                table_slots[best_table] -= 1
        return assignments
