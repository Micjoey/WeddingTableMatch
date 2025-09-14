from dataclasses import dataclass
from typing import List


@dataclass
class Guest:
    """Represents a wedding guest."""
    name: str
    single: bool
    gender_identity: str
    interested_in: List[str]
    min_known_neighbors: int
    min_unknown_neighbors: int


@dataclass
class Table:
    """Represents a table at the wedding."""
    name: str
    capacity: int


@dataclass
class Relationship:
    """Represents a relationship between two guests."""
    a: str
    b: str
    relation: str
    strength: int
