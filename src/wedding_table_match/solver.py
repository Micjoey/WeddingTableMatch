"""Simple seating solver placeholder."""
from __future__ import annotations

from typing import Dict, List

from .models import Guest, Table, Relationship


class SeatingModel:
    """Very small seating solver.

    The solver currently performs a naive round-robin assignment of guests to
    tables and does not use the relationship information.  It serves as a
    placeholder for a future optimisation model.
    """

    def __init__(self) -> None:
        self.guests: List[Guest] = []
        self.tables: List[Table] = []
        self.relationships: Dict[tuple[str, str], Relationship] = {}

    def build(
        self, guests: List[Guest], tables: List[Table], relationships: List[Relationship]
    ) -> None:
        """Store model data for later solving."""
        self.guests = guests
        self.tables = tables
        self.relationships = {(r.a, r.b): r for r in relationships}

    def get_relationship(self, a: str, b: str) -> Relationship:
        """Return relationship for a pair, defaulting to neutral."""
        rel = self.relationships.get((a, b)) or self.relationships.get((b, a))
        if rel:
            return rel
        return Relationship(a=a, b=b, relation="neutral", strength=0, notes="")

    def solve(self) -> Dict[str, str]:
        """Assign guests to tables using round-robin by capacity."""
        assignments: Dict[str, str] = {}
        table_slots = {t.name: t.capacity for t in self.tables}
        table_names = [t.name for t in self.tables]
        if not table_names:
            return assignments

        index = 0
        for guest in self.guests:
            placed = False
            rotations = 0
            while not placed:
                table_name = table_names[index % len(table_names)]
                if table_slots[table_name] > 0:
                    assignments[guest.name] = table_name
                    table_slots[table_name] -= 1
                    placed = True
                else:
                    index += 1
                    rotations += 1
                    if rotations > len(table_names):
                        raise ValueError("Not enough seats for all guests")
            index += 1
        return assignments
