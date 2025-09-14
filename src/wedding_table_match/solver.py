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

    def __init__(self) -> None:
        self.guests: List[Guest] = []
        self.tables: List[Table] = []
        self.relationships: Dict[Tuple[str, str], Relationship] = {}
        self.must_separate: Dict[str, Set[str]] = {}

    def build(
        self, guests: List[Guest], tables: List[Table], relationships: List[Relationship]
    ) -> None:
        """Store model data for later solving."""
        self.guests = guests
        self.tables = tables
        # Store relationships in both directions for easy lookup
        self.relationships = {}
        for r in relationships:
            self.relationships[(r.a, r.b)] = r
            self.relationships[(r.b, r.a)] = Relationship(
                a=r.b, b=r.a, relation=r.relation, strength=r.strength, notes=r.notes
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
        """Return (feasible, score) for seating ``group`` at ``table_name``."""
        if table_slots[table_name] < len(group):
            return False, 0

        score = 0
        for member in group:
            for other, other_table in assignments.items():
                if other_table != table_name:
                    continue
                if other in self.must_separate.get(member, set()):
                    return False, 0
                rel = self.get_relationship(member, other)
                if rel.relation == "avoid":
                    return False, 0
                if rel.relation == "know":
                    score += rel.strength
        return True, score

    # ------------------------------------------------------------------
    def solve(self) -> Dict[str, str]:
        """Assign guests to tables using a relationship aware heuristic."""
        assignments: Dict[str, str] = {}
        table_slots = {t.name: t.capacity for t in self.tables}
        groups = self._build_groups()

        for group in groups:
            best_table = None
            best_score = -1
            for table in self.tables:
                feasible, score = self._table_score(group, table.name, assignments, table_slots)
                if feasible and score > best_score:
                    best_table = table.name
                    best_score = score
            if best_table is None:
                raise ValueError("No valid table for group: " + ", ".join(group))
            for member in group:
                assignments[member] = best_table
                table_slots[best_table] -= 1
        return assignments

