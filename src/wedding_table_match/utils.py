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
    "neutral": 0,
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
    """Beam search seating solver with local swaps and size balancing."""

    def __init__(
        self,
        maximize_known: bool = False,
        group_singles: bool = False,
        min_known: int = 0,
        group_by_meal_preference: bool = False,
        balance_tables: bool = False,
        balance_weight: float = 8.0,
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
        self.group_by_meal_preference = group_by_meal_preference
        # Size balancing
        self.balance_tables = balance_tables
        self.balance_weight = float(balance_weight)
        self.target_size: Dict[str, int] = {}  # set in build
        # Id mapping helpers
        self.id_by_name: Dict[str, str] = {}
        self.name_by_id: Dict[str, str] = {}

    def build(
        self, guests: List[Guest], tables: List[Table], relationships: List[Relationship]
    ) -> None:
        """Store model data and precompute targets for balancing."""
        self.guests = guests
        self.tables = tables
        self.id_by_name = {g.name: g.id for g in guests}
        self.name_by_id = {g.id: g.name for g in guests}

        # Index relationships by both ids and names for robustness
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

        # Targets for size balancing
        self._compute_target_sizes()

    # ----------------------------- helpers -----------------------------
    def _compute_target_sizes(self) -> None:
        """Compute near-equal per table target sizes that sum to guest count and respect capacities."""
        total_guests = len(self.guests)
        if not self.tables or total_guests == 0:
            self.target_size = {}
            return

        names = [t.name for t in self.tables]
        cap = {t.name: int(t.capacity) for t in self.tables}
        T = len(names)

        base = total_guests // T
        rem = total_guests % T

        target = {t: min(cap[t], base) for t in names}
        # Give one extra to rem tables with most headroom
        headroom = sorted(names, key=lambda n: cap[n] - target[n], reverse=True)
        for t in headroom:
            if rem <= 0:
                break
            if target[t] < cap[t]:
                target[t] += 1
                rem -= 1

        # If we still need to place more because some caps were tight
        placed = sum(target.values())
        need = total_guests - placed
        if need > 0:
            # Fill more into tables with headroom
            headroom = sorted(names, key=lambda n: cap[n] - target[n], reverse=True)
            i = 0
            while need > 0 and i < len(headroom):
                t = headroom[i]
                if target[t] < cap[t]:
                    target[t] += 1
                    need -= 1
                else:
                    i += 1

        self.target_size = target

    def get_relationship(self, a: str, b: str) -> Relationship:
        """Return relationship for a pair. Defaults to neutral when unknown."""
        return self.relationships.get((a, b)) or Relationship(a=a, b=b, relation="neutral", strength=0, notes="")

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
        """Hard checks only."""
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

    def _table_delta(self, group: List[str], table_name: str, assignments: Dict[str, str], table_slots: Dict[str, int]) -> float:
        """Change in total objective if we seat group at table_name.

        Objective:
          1. Pair score totals across tables.
          2. Soft bonus for meeting min_known per member.
          3. Soft size balancing penalty relative to per table target.
        """
        existing = [name for name, t in assignments.items() if t == table_name]
        combined = existing + group

        # Old and new pair totals at this table
        old_total = compute_table_stats(existing, self.get_relationship)["total_score"] if len(existing) >= 2 else 0
        new_total = compute_table_stats(combined, self.get_relationship)["total_score"]
        delta = float(new_total - old_total)

        # Soft known bonus
        if self.min_known > 0:
            for member in group:
                known = 0
                for other in combined:
                    if other == member:
                        continue
                    if relation_value(self.get_relationship(member, other)) > 0:
                        known += 1
                if known >= self.min_known:
                    delta += 6.0  # tuned small to avoid overpowering pair scores

        # Size balancing
        if self.balance_tables and self.target_size:
            tgt = self.target_size.get(table_name, 0)
            old_size = len(existing)
            new_size = len(combined)
            # Penalty change relative to absolute deviation
            before = abs(old_size - tgt)
            after = abs(new_size - tgt)
            delta += self.balance_weight * float(before - after)

        return delta

    def _optimize_assignments(self, assignments: Dict[str, str], table_slots: Dict[str, int]) -> Dict[str, str]:
        """Local pair swap hill climb. Respects hard constraints."""
        improved = True
        iters = 0
        while improved and iters < 12:
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

                    # Feasibility checks
                    group1 = [n for n, t in new_assign.items() if t == t1]
                    group2 = [n for n, t in new_assign.items() if t == t2]
                    if not self._feasible_with(group1, t1, {k: v for k, v in new_assign.items() if v == t1}, {t1: len(group1)}):
                        continue
                    if not self._feasible_with(group2, t2, {k: v for k, v in new_assign.items() if v == t2}, {t2: len(group2)}):
                        continue

                    # Objective change: compute per-table totals and size penalties
                    def total_obj(members: List[str], table: str) -> float:
                        score = compute_table_stats(members, self.get_relationship)["total_score"]
                        if self.balance_tables and self.target_size:
                            tgt = self.target_size.get(table, 0)
                            score += self.balance_weight * float(-abs(len(members) - tgt))
                        return score

                    old1 = total_obj([n for n, t in assignments.items() if t == t1], t1)
                    old2 = total_obj([n for n, t in assignments.items() if t == t2], t2)
                    new1 = total_obj(group1, t1)
                    new2 = total_obj(group2, t2)

                    if new1 + new2 > old1 + old2:
                        assignments = new_assign
                        improved = True
                        # continue to search for more improvements
        return assignments

    # ----------------------------- solve -----------------------------
    def solve(self) -> Dict[str, str]:
        """Assign guests to tables using beam search with greedy fallback and swaps."""
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
        beam: List[Tuple[Dict[str, str], Dict[str, int], float]] = [({}, initial_slots, 0.0)]
        beam_width = 8  # wider search for better compatibility

        for group in groups:
            next_beam: List[Tuple[Dict[str, str], Dict[str, int], float]] = []
            for assignments, table_slots, cum_score in beam:
                candidates: List[Tuple[str, float]] = []
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

        # Local improvement
        assignments = self._optimize_assignments(assignments, table_slots)
        return assignments
