"""Relationship aware seating solver."""
from __future__ import annotations

from typing import Dict, List, Set, Tuple

from .models import Guest, Table, Relationship



class SeatingModel:
    """Greedy seating solver that honours simple relationship rules.

    The solver groups guests that must sit together, avoids placing guests
    that must be separated, and prefers tables where guests know more people.
    It is intentionally small and easy to understand rather than optimal.
    """

    def __init__(self, maximize_known: bool = False, group_singles: bool = False, min_known: int = 0, group_by_meal_preference: bool = False) -> None:
        self.guests: List[Guest] = []
        self.tables: List[Table] = []
        self.relationships: Dict[Tuple[str, str], Relationship] = {}
        self.must_separate: Dict[str, Set[str]] = {}
        self.maximize_known = maximize_known
        self.group_singles = group_singles
        self.min_known = min_known
        self.group_by_meal_preference = group_by_meal_preference
        # Maps to reconcile id/name differences across inputs
        self.id_by_name: Dict[str, str] = {}
        self.name_by_id: Dict[str, str] = {}

    def build(
        self, guests: List[Guest], tables: List[Table], relationships: List[Relationship]
    ) -> None:
        """Store model data for later solving."""
        self.guests = guests
        self.tables = tables
        # Build id/name maps
        self.id_by_name = {g.name: g.id for g in guests}
        self.name_by_id = {g.id: g.name for g in guests}

        # Store relationships in both directions for easy lookup
        # Index by both ids and names to be robust to CSV schema differences.
        self.relationships = {}
        for r in relationships:
            a_variants = {r.a}
            b_variants = {r.b}
            # If provided ids, add corresponding names
            if r.a in self.name_by_id:
                a_variants.add(self.name_by_id[r.a])
            # If provided names, add corresponding ids
            if r.a in self.id_by_name:
                a_variants.add(self.id_by_name[r.a])
            if r.b in self.name_by_id:
                b_variants.add(self.name_by_id[r.b])
            if r.b in self.id_by_name:
                b_variants.add(self.id_by_name[r.b])

            for a_key in a_variants:
                for b_key in b_variants:
                    self.relationships[(a_key, b_key)] = Relationship(
                        a=a_key, b=b_key, relation=r.relation, strength=r.strength, notes=r.notes
                    )
                    self.relationships[(b_key, a_key)] = Relationship(
                        a=b_key, b=a_key, relation=r.relation, strength=r.strength, notes=r.notes
                    )
        # Build symmetric must_separate map
        self.must_separate = {g.name: set(g.must_separate) for g in guests}
        for g in guests:
            for other in g.must_separate:
                self.must_separate.setdefault(other, set()).add(g.name)

    def get_relationship(self, a: str, b: str) -> Relationship:
        """Return relationship for a pair, defaulting to neutral."""
        return self.relationships.get((a, b)) or Relationship(
            a=a, b=b, relation="neutral", strength=0, notes=""
        )

    # ------------------------------------------------------------------
    # Helper methods
    def _build_groups(self) -> List[List[str]]:
        """Group guests connected by ``must_with`` relationships."""
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

        # Sort members and groups for deterministic behaviour
        return sorted(
            [sorted(members) for members in groups.values()],
            key=lambda g: (-len(g), g[0]),
        )

    def _table_score(
        self,
        group: List[str],
        table_name: str,
        assignments: Dict[str, str],
        table_slots: Dict[str, int],
    ) -> Tuple[bool, int]:
        """Return (feasible, score) for seating ``group`` at ``table_name``.
        If min_known > 0, require each member to have at least min_known 'know' relationships at the table (if possible)."""
        if table_slots[table_name] < len(group):
            return False, 0

        score = 0
        table_members = [other for other, t in assignments.items() if t == table_name] + group
        for member in group:
            # Check must_separate and avoid
            for other in table_members:
                if other == member:
                    continue
                if other in self.must_separate.get(member, set()):
                    return False, 0
                rel = self.get_relationship(member, other)
                if rel.relation == "avoid":
                    return False, 0
        # Check min_known constraint
        if self.min_known > 0:
            for member in group:
                known_count = 0
                for other in table_members:
                    if other == member:
                        continue
                    rel = self.get_relationship(member, other)
                    if rel.relation == "know":
                        known_count += 1
                if known_count < self.min_known:
                    return False, 0
        # Scoring
        for member in group:
            for other in table_members:
                if other == member:
                    continue
                rel = self.get_relationship(member, other)
                if self.maximize_known and rel.relation == "know":
                    score += rel.strength
                elif rel.relation == "know":
                    score += 1
        return True, score

    # ------------------------------------------------------------------
    def solve(self) -> Dict[str, str]:
        """Assign guests to tables with a relationship-aware beam search.

        Uses a small beam to reduce greedy pitfalls while honoring
        must_with, must_separate, avoid and min_known. Falls back to
        a relaxed greedy pass if strict placement fails.
        """
        groups = self._build_groups()

        # Optionally group by meal preference
        if self.group_by_meal_preference:
            meal_groups = {}
            for g in groups:
                for name in g:
                    guest = next((guest for guest in self.guests if guest.name == name), None)
                    if guest:
                        meal = getattr(guest, "meal_preference", "")
                        meal_groups.setdefault(meal, []).append(name)
            # Only use non-empty groups
            groups = [sorted(members) for members in meal_groups.values() if members]

        # Optionally group singles together by preference
        if self.group_singles:
            singles_guests = [g for g in self.guests if getattr(g, "single", False)]
            # Group singles by interested_in and gender_identity compatibility
            singles_groups: List[List[str]] = []
            used = set()
            for i, g1 in enumerate(singles_guests):
                if g1.name in used:
                    continue
                group = [g1.name]
                used.add(g1.name)
                for j, g2 in enumerate(singles_guests):
                    if i == j or g2.name in used:
                        continue
                    # Check if g1 and g2 are mutually interested
                    if (
                        g2.gender_identity in g1.interested_in or not g1.interested_in
                    ) and (
                        g1.gender_identity in g2.interested_in or not g2.interested_in
                    ):
                        group.append(g2.name)
                        used.add(g2.name)
                singles_groups.append(group)
            # Remove singles from other groups
            non_singles = [g for g in groups if not any(name in [sg.name for sg in singles_guests] for name in g)]
            if singles_groups:
                groups = non_singles + singles_groups

        # Beam search state: (assignments, table_slots, cumulative_score)
        from heapq import nlargest

        initial_slots = {t.name: t.capacity for t in self.tables}
        beam: List[Tuple[Dict[str, str], Dict[str, int], int]] = [({}, initial_slots, 0)]
        beam_width = 5

        for group in groups:
            next_beam: List[Tuple[Dict[str, str], Dict[str, int], int]] = []
            for assignments, table_slots, cum_score in beam:
                # Consider all feasible tables for this group
                candidates: List[Tuple[str, int]] = []
                for table in self.tables:
                    feasible, delta = self._table_score(group, table.name, assignments, table_slots)
                    if feasible:
                        candidates.append((table.name, delta))

                if not candidates:
                    continue

                # Try top-k candidates for this state
                candidates.sort(key=lambda x: x[1], reverse=True)
                for table_name, delta in candidates[:beam_width]:
                    new_assignments = dict(assignments)
                    new_slots = dict(table_slots)
                    for member in group:
                        new_assignments[member] = table_name
                        new_slots[table_name] -= 1
                    next_beam.append((new_assignments, new_slots, cum_score + delta))

            if not next_beam:
                # Could not place this group strictly in any beam state; break to fallback
                beam = []
                break

            # Keep best beam_width states overall
            next_beam = nlargest(beam_width, next_beam, key=lambda s: s[2])
            beam = next_beam

        if beam:
            best_assignments, _, _ = max(beam, key=lambda s: s[2])
            return best_assignments

        # Fallback: relaxed greedy similar to previous implementation
        assignments: Dict[str, str] = {}
        table_slots = {t.name: t.capacity for t in self.tables}
        unassigned_groups = []
        for group in groups:
            best_table = None
            best_score = -1
            for table in self.tables:
                feasible, score = self._table_score(group, table.name, assignments, table_slots)
                if feasible and score > best_score:
                    best_table = table.name
                    best_score = score
            if best_table is None:
                unassigned_groups.append(group)
            else:
                for member in group:
                    assignments[member] = best_table
                    table_slots[best_table] -= 1

        # Relax constraints for remaining groups (ignore must_separate/avoid/min_known)
        for group in unassigned_groups:
            best_table = None
            best_score = -1
            for table in self.tables:
                if table_slots[table.name] < len(group):
                    continue
                score = 0
                for member in group:
                    for other, other_table in assignments.items():
                        if other_table != table.name:
                            continue
                        rel = self.get_relationship(member, other)
                        if self.maximize_known and rel.relation == "know":
                            score += rel.strength
                        elif rel.relation == "know":
                            score += 1
                if score > best_score:
                    best_table = table.name
                    best_score = score
            if best_table is None:
                raise ValueError("No valid table for group (even with relaxed constraints): " + ", ".join(group))
            for member in group:
                # Mark fallback assignments with an asterisk
                assignments[member + "*"] = best_table
                table_slots[best_table] -= 1
        return assignments
