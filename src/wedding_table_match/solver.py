"""
Relationship aware seating solver with strong size equalization.

Relationship values:
    best friend: +5
    friend: +3
    know: +2
    neutral: 0
    avoid: -3
    conflict: -5
"""
from __future__ import annotations

from itertools import combinations
from typing import Callable, Dict, List, Set, Tuple

from .models import Guest, Table, Relationship


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


class SeatingModel:
    """Beam search with quadratic equalization and postsolve rebalancing."""

    def __init__(
        self,
        maximize_known: bool = False,
        group_singles: bool = False,
        min_known: int = 0,
        group_by_meal_preference: bool = False,
        equalize_tables: bool = False,
        balance_weight: float = 12.0,
        min_target_slack: int = 0,
    ) -> None:
        self.guests: List[Guest] = []
        self.tables: List[Table] = []
        self.relationships: Dict[Tuple[str, str], Relationship] = {}
        self.must_separate: Dict[str, Set[str]] = {}

        self.maximize_known = maximize_known
        self.group_singles = group_singles
        self.min_known = min_known
        self.group_by_meal_preference = group_by_meal_preference

        self.equalize_tables = equalize_tables
        self.balance_weight = float(balance_weight)
        self.min_target_slack = int(min_target_slack)
        self.target_size: Dict[str, int] = {}

        self.id_by_name: Dict[str, str] = {}
        self.name_by_id: Dict[str, str] = {}

    # ----------------------------- build -----------------------------
    def build(
        self, guests: List[Guest], tables: List[Table], relationships: List[Relationship]
    ) -> None:
        self.guests = guests
        self.tables = tables
        self.id_by_name = {g.name: g.id for g in guests}
        self.name_by_id = {g.id: g.name for g in guests}

        # Store relationships robustly across id or name
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

        # Symmetric must_separate
        self.must_separate = {g.name: set(g.must_separate) for g in guests}
        for g in guests:
            for other in g.must_separate:
                self.must_separate.setdefault(other, set()).add(g.name)

        self._compute_target_sizes()

    def _compute_target_sizes(self) -> None:
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
        # Give extras to rem tables with most headroom
        headroom = sorted(names, key=lambda n: cap[n] - target[n], reverse=True)
        for t in headroom:
            if rem <= 0:
                break
            if target[t] < cap[t]:
                target[t] += 1
                rem -= 1

        # If caps limited us, fill remaining greedily
        placed = sum(target.values())
        need = total_guests - placed
        if need > 0:
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

    # ----------------------------- helpers -----------------------------
    def get_relationship(self, a: str, b: str) -> Relationship:
        return self.relationships.get((a, b)) or Relationship(a=a, b=b, relation="neutral", strength=0, notes="")

    def _build_groups(self) -> List[List[str]]:
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

    def _size_penalty(self, size: int, target: int) -> float:
        """Quadratic penalty on deviation. Slack around target is free."""
        d = abs(size - target)
        if d <= self.min_target_slack:
            return 0.0
        d_adj = d - self.min_target_slack
        return self.balance_weight * float(d_adj * d_adj)

    def _table_delta(self, group: List[str], table_name: str, assignments: Dict[str, str], table_slots: Dict[str, int]) -> float:
        existing = [name for name, t in assignments.items() if t == table_name]
        combined = existing + group

        # Pair totals
        old_total = compute_table_stats(existing, self.get_relationship)["total_score"] if len(existing) >= 2 else 0
        new_total = compute_table_stats(combined, self.get_relationship)["total_score"]
        delta = float(new_total - old_total)

        # Small bonus for meeting min_known
        if self.min_known > 0:
            for member in group:
                known = 0
                for other in combined:
                    if other == member:
                        continue
                    if relation_value(self.get_relationship(member, other)) > 0:
                        known += 1
                if known >= self.min_known:
                    delta += 6.0

        # Size equalization
        if self.equalize_tables and self.target_size:
            tgt = self.target_size.get(table_name, 0)
            before = self._size_penalty(len(existing), tgt)
            after = self._size_penalty(len(combined), tgt)
            delta += float(before - after)

        return delta

    def _objective_total(self, table_to_members: Dict[str, List[str]]) -> float:
        """Total objective across tables with size penalties."""
        total = 0.0
        for t, members in table_to_members.items():
            total += compute_table_stats(members, self.get_relationship)["total_score"]
            if self.equalize_tables and self.target_size:
                total -= self._size_penalty(len(members), self.target_size.get(t, 0))
        return total

    def _optimize_assignments(self, assignments: Dict[str, str]) -> Dict[str, str]:
        """Local pair swap hill climb under hard constraints."""
        improved = True
        iters = 0
        while improved and iters < 14:
            improved = False
            iters += 1
            guest_list = list(assignments.keys())
            # Precompute current groups
            tab_members: Dict[str, List[str]] = {}
            for g, t in assignments.items():
                tab_members.setdefault(t, []).append(g)
            base_obj = self._objective_total(tab_members)

            for i in range(len(guest_list)):
                for j in range(i + 1, len(guest_list)):
                    g1, g2 = guest_list[i], guest_list[j]
                    t1, t2 = assignments[g1], assignments[g2]
                    if t1 == t2:
                        continue

                    # Tentative swap
                    tab_members[t1].remove(g1)
                    tab_members[t2].remove(g2)
                    tab_members[t1].append(g2)
                    tab_members[t2].append(g1)

                    # Hard feasibility check
                    if not self._feasible_with(tab_members[t1], t1, {k: v for k, v in assignments.items() if v == t1 or k in (g1, g2)}, {t1: len(tab_members[t1])}):
                        tab_members[t1].remove(g2)
                        tab_members[t2].remove(g1)
                        tab_members[t1].append(g1)
                        tab_members[t2].append(g2)
                        continue
                    if not self._feasible_with(tab_members[t2], t2, {k: v for k, v in assignments.items() if v == t2 or k in (g1, g2)}, {t2: len(tab_members[t2])}):
                        tab_members[t1].remove(g2)
                        tab_members[t2].remove(g1)
                        tab_members[t1].append(g1)
                        tab_members[t2].append(g2)
                        continue

                    new_obj = self._objective_total(tab_members)
                    if new_obj > base_obj:
                        assignments[g1], assignments[g2] = t2, t1
                        base_obj = new_obj
                        improved = True
                    else:
                        # revert
                        tab_members[t1].remove(g2)
                        tab_members[t2].remove(g1)
                        tab_members[t1].append(g1)
                        tab_members[t2].append(g2)
            # continue until no improvement
        return assignments

    def _rebalance_to_targets(self, assignments: Dict[str, str]) -> Dict[str, str]:
        """Move guests from overfull vs target to underfull vs target while preserving score."""
        if not self.equalize_tables or not self.target_size:
            return assignments

        # Build members per table
        table_members: Dict[str, List[str]] = {}
        for g, t in assignments.items():
            table_members.setdefault(t, []).append(g)

        def deviation(t: str) -> int:
            return len(table_members.get(t, [])) - self.target_size.get(t, 0)

        # Try to fix largest gaps first
        moved = True
        tries = 0
        while moved and tries < 50:
            moved = False
            tries += 1
            over_tables = sorted([t for t in table_members if deviation(t) > 0], key=lambda t: deviation(t), reverse=True)
            under_tables = sorted([t for t in table_members if deviation(t) < 0], key=lambda t: deviation(t))

            if not over_tables or not under_tables:
                break

            improved_any = False
            for t_from in over_tables:
                for t_to in under_tables:
                    # Try moving one guest that hurts least to remove and helps most to add
                    best_gain = None
                    best_guest = None

                    for g in list(table_members[t_from]):
                        # Remove g from from-table
                        cand_from = [x for x in table_members[t_from] if x != g]
                        cand_to = table_members[t_to] + [g]

                        # Check hard constraints for t_to
                        feasible = True
                        for other in cand_to:
                            if other == g:
                                continue
                            if other in self.must_separate.get(g, set()):
                                feasible = False
                                break
                            rel = self.get_relationship(g, other)
                            if rel.relation == "avoid":
                                feasible = False
                                break
                        if not feasible:
                            continue

                        # Objective delta
                        before = self._objective_total({
                            t_from: table_members[t_from],
                            t_to: table_members[t_to],
                        })
                        after = self._objective_total({
                            t_from: cand_from,
                            t_to: cand_to,
                        })
                        gain = after - before
                        if best_gain is None or gain > best_gain:
                            best_gain = gain
                            best_guest = g

                    if best_guest is not None and (best_gain is not None and best_gain >= -0.5):
                        # Accept small negative if it improves equalization
                        table_members[t_from].remove(best_guest)
                        table_members[t_to].append(best_guest)
                        assignments[best_guest] = t_to
                        moved = True
                        improved_any = True
                        # Update lists if targets are met
                        if deviation(t_from) <= 0 or deviation(t_to) >= 0:
                            break
                if improved_any:
                    break
        return assignments

    # ----------------------------- solve -----------------------------
    def solve(self) -> Dict[str, str]:
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

        # Split groups larger than any table
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
        beam_width = 10

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
            best_assign, _, _ = max(beam, key=lambda s: s[2])
        else:
            # Greedy fallback
            best_assign: Dict[str, str] = {}
            table_slots = {t.name: t.capacity for t in self.tables}
            for group in groups:
                best_table = None
                best_delta = None
                for table in self.tables:
                    if not self._feasible_with(group, table.name, best_assign, table_slots):
                        continue
                    delta = self._table_delta(group, table.name, best_assign, table_slots)
                    if best_delta is None or delta > best_delta:
                        best_delta = delta
                        best_table = table.name
                if best_table is None:
                    raise ValueError(f"No valid table for group: {', '.join(group)}")
                for member in group:
                    best_assign[member] = best_table
                    table_slots[best_table] -= 1

        # Local swaps
        best_assign = self._optimize_assignments(best_assign)
        # Rebalance toward targets
        best_assign = self._rebalance_to_targets(best_assign)
        return best_assign
