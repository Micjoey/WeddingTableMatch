"""
Relationship aware seating solver.

Relationship scale for table grading:
    best friend: +5
    friend: +3
    know: +2
    neutral: 0
    avoid: -3
    conflict: -5
Table compatibility is graded A–F based on the average relationship score among all pairs at the table.
"""
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
        Uses the full relationship scale for scoring (maximize compatibility)."""
        if table_slots[table_name] < len(group):
            return False, 0

        score = 0
        table_members = [other for other, t in assignments.items() if t == table_name] + group
        # Check must_separate and avoid
        for member in group:
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
        # Scoring: use full relationship scale
        relation_scale = {
            'best friend': 5,
            'friend': 3,
            'know': 2,
            'neutral': 0,
            'avoid': -3,
            'conflict': -5,
        }
        for i, member in enumerate(group):
            for j, other in enumerate(table_members):
                if other == member or j <= i:
                    continue
                rel = self.get_relationship(member, other)
                score += relation_scale.get(rel.relation, rel.strength if hasattr(rel, 'strength') else 0)
        return True, score

    # ------------------------------------------------------------------
    def solve(self) -> Dict[str, str]:
        """Assign guests to tables with a relationship-aware beam search.

        Uses a small beam to reduce greedy pitfalls while honoring
        must_with, must_separate, avoid and min_known. Falls back to
        a relaxed greedy pass if strict placement fails.
        """
        print("[DEBUG] SeatingModel.solve() called")
        print("[DEBUG] All guests loaded:")
        for g in self.guests:
            print(f"  - {g.name}: single={getattr(g, 'single', None)}, interested_in={getattr(g, 'interested_in', None)}, gender_identity={getattr(g, 'gender_identity', None)}")
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
            print("[DEBUG] singles_guests:", [g.name for g in singles_guests])
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
            print("[DEBUG] singles_groups:", singles_groups)
            # Remove singles from other groups
            non_singles = [g for g in groups if not any(name in [sg.name for sg in singles_guests] for name in g)]
            if singles_groups:
                groups = non_singles + singles_groups
            print("[DEBUG] Groups after singles grouping:", groups)

        # Beam search state: (assignments, table_slots, cumulative_score)
        from heapq import nlargest

        initial_slots = {t.name: t.capacity for t in self.tables}
        beam: List[Tuple[Dict[str, str], Dict[str, int], int]] = [({}, initial_slots, 0)]
        beam_width = 5

        for group in groups:
            print(f"[DEBUG] Considering group: {group}")
            next_beam: List[Tuple[Dict[str, str], Dict[str, int], int]] = []
            for assignments, table_slots, cum_score in beam:
                # Consider all feasible tables for this group
                candidates: List[Tuple[str, int]] = []
                for table in self.tables:
                    feasible, delta = self._table_score(group, table.name, assignments, table_slots)
                    print(f"[DEBUG]   Table '{table.name}': feasible={feasible}, score={delta}")
                    if feasible:
                        candidates.append((table.name, delta))

                if not candidates:
                    print(f"[DEBUG]   No feasible tables for group {group} in this beam state.")
                    continue

                # Try top-k candidates for this state
                candidates.sort(key=lambda x: x[1], reverse=True)
                for table_name, delta in candidates[:beam_width]:
                    new_assignments = dict(assignments)
                    new_slots = dict(table_slots)
                    for member in group:
                        new_assignments[member] = table_name
                        new_slots[table_name] -= 1
                    print(f"[DEBUG]   Assigning group {group} to table '{table_name}' with score {delta}")
                    next_beam.append((new_assignments, new_slots, cum_score + delta))

            if not next_beam:
                print(f"[DEBUG] No beam states could place group {group}. Triggering fallback.")
                beam = []
                break

            # Keep best beam_width states overall
            next_beam = nlargest(beam_width, next_beam, key=lambda s: s[2])
            beam = next_beam

        if beam:
            best_assignments, _, _ = max(beam, key=lambda s: s[2])
            print(f"[DEBUG] Main assignment succeeded. Assignments: {best_assignments}")
            return best_assignments

        # Fallback: relaxed greedy similar to previous implementation
        print("[DEBUG] Entering fallback assignment mode.")
        assignments: Dict[str, str] = {}
        table_slots = {t.name: t.capacity for t in self.tables}
        unassigned_groups = []
        for group in groups:
            print(f"[DEBUG] [Fallback] Considering group: {group}")
            best_table = None
            best_score = -1
            for table in self.tables:
                feasible, score = self._table_score(group, table.name, assignments, table_slots)
                print(f"[DEBUG]   Table '{table.name}': feasible={feasible}, score={score}")
                if feasible and score > best_score:
                    best_table = table.name
                    best_score = score
            if best_table is None:
                print(f"[DEBUG]   No feasible table for group {group} in fallback. Will try relaxing constraints.")
                unassigned_groups.append(group)
            else:
                print(f"[DEBUG]   Assigning group {group} to table '{best_table}' with score {best_score}")
                for member in group:
                    assignments[member] = best_table
                    table_slots[best_table] -= 1

        # Relax constraints for remaining groups (ignore must_separate/avoid/min_known)
        for group in unassigned_groups:
            print(f"[DEBUG] [Fallback Relaxed] Considering group: {group}")
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
                print(f"[DEBUG]   Table '{table.name}': relaxed score={score}")
                if score > best_score:
                    best_table = table.name
                    best_score = score
            if best_table is None:
                print(f"[DEBUG]   No valid table for group {group} even after relaxing constraints.")
                raise ValueError("No valid table for group (even with relaxed constraints): " + ", ".join(group))
            print(f"[DEBUG]   Assigning group {group} to table '{best_table}' with relaxed score {best_score} (asterisk)")
            for member in group:
                # Mark fallback assignments with an asterisk
                assignments[member + "*"] = best_table
                table_slots[best_table] -= 1
        print(f"[DEBUG] Final fallback assignments: {assignments}")
        return assignments
