"""Data models for WeddingTableMatch."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List
import math


def parse_pipe_list(value: object) -> List[str]:
    """Split a pipe separated string into a list.

    Empty values such as ``""`` or ``None`` return an empty list.
    ``pandas`` often provides ``float('nan')`` for missing values which is
    also treated as empty.
    """
    if value is None:
        return []
    if isinstance(value, float) and math.isnan(value):
        return []
    text = str(value).strip()
    if not text or text.lower() == "nan":
        return []
    return [part.strip() for part in text.split("|") if part.strip()]


def parse_bool(value: object) -> bool:
    """Parse common truthy strings into bool."""
    return str(value).strip().lower() == "true"


def parse_interested_in(value: object) -> List[str]:
    """Parse the ``interested_in`` column."""
    return parse_pipe_list(value)


@dataclass
class Guest:
    """Representation of a wedding guest."""

    id: str
    name: str
    age: int = 0
    gender_identity: str = ""
    rsvp: str = ""
    meal_preference: str = ""
    single: bool = False
    interested_in: List[str] = field(default_factory=list)
    plus_one: bool = False
    sit_with_partner: bool = True
    min_known: int = 0
    min_unknown: int = 0
    weight: int = 1
    must_with: List[str] = field(default_factory=list)
    must_separate: List[str] = field(default_factory=list)
    groups: List[str] = field(default_factory=list)


@dataclass
class Table:
    """Dinner table definition."""

    name: str
    capacity: int
    tags: List[str] = field(default_factory=list)


@dataclass
class Relationship:
    """Relationship between two guests."""

    a: str
    b: str
    relation: str
    strength: int = 0
    notes: str = ""
