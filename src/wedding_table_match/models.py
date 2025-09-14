"""
Data models for wedding table matching.

This module contains the core data structures for representing guests,
tables, and relationships in the wedding seating optimization problem.
"""

from dataclasses import dataclass
from typing import List, Optional
from enum import Enum


class RelationshipType(Enum):
    """Types of relationships between guests."""
    FAMILY = "family"
    FRIEND = "friend"
    COLLEAGUE = "colleague"
    PLUS_ONE = "plus_one"
    AVOID = "avoid"


@dataclass
class Guest:
    """Represents a wedding guest."""
    id: int
    name: str
    age: Optional[int] = None
    dietary_restrictions: Optional[str] = None
    
    def __str__(self) -> str:
        return f"Guest({self.id}: {self.name})"


@dataclass
class Table:
    """Represents a table at the wedding venue."""
    id: int
    name: str
    capacity: int
    location: Optional[str] = None
    
    def __str__(self) -> str:
        return f"Table({self.id}: {self.name}, capacity={self.capacity})"


@dataclass
class Relationship:
    """Represents a relationship between two guests."""
    guest1_id: int
    guest2_id: int
    relationship_type: RelationshipType
    strength: float = 1.0  # Relationship strength (0.0 to 1.0)
    
    def __str__(self) -> str:
        return f"Relationship({self.guest1_id} <-> {self.guest2_id}: {self.relationship_type.value})"


class SeatingArrangement:
    """Represents a complete seating arrangement solution."""
    
    def __init__(self):
        self.assignments: dict[int, int] = {}  # guest_id -> table_id
        self.score: float = 0.0
        
    def assign_guest_to_table(self, guest_id: int, table_id: int) -> None:
        """Assign a guest to a table."""
        self.assignments[guest_id] = table_id
        
    def get_table_for_guest(self, guest_id: int) -> Optional[int]:
        """Get the table assignment for a guest."""
        return self.assignments.get(guest_id)
        
    def get_guests_at_table(self, table_id: int) -> List[int]:
        """Get all guests assigned to a specific table."""
        return [guest_id for guest_id, tid in self.assignments.items() if tid == table_id]
        
    def __str__(self) -> str:
        return f"SeatingArrangement(assignments={len(self.assignments)}, score={self.score})"