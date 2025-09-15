"""CSV loading utilities."""
from __future__ import annotations

from pathlib import Path
from typing import Iterable, List

import pandas as pd

from .models import Guest, Table, Relationship, parse_pipe_list, parse_bool


def _ensure_path(path: Path | str) -> Path:
    return Path(path)


from typing import IO, Any

def load_guests(path: Path | str | IO[Any]) -> List[Guest]:
    """Load guests from ``guests.csv``.

    Validates that any ``must_with`` and ``must_separate`` references exist.
    """
    df = pd.read_csv(path)
    guests: List[Guest] = []
    for _, row in df.iterrows():
        gender_identity = row.get("gender_identity", "")
        # Fallback for legacy CSVs: use 'gender' if 'gender_identity' is missing
        if not gender_identity and "gender" in row:
            gender_identity = row.get("gender", "")
        plus_one_val = row.get("plus_one", "false")
        plus_one = parse_bool(plus_one_val)
        # Only set sit_with_partner if plus_one is true
        sit_with_partner_val = row.get("sit_with_partner", "true")
        sit_with_partner = parse_bool(sit_with_partner_val) if plus_one else False
        guest = Guest(
            id=str(row["id"]),
            name=row["name"],
            age=int(row.get("age", 0)),
            gender_identity=gender_identity,
            rsvp=row.get("rsvp", ""),
            meal_preference=row.get("meal_preference", ""),
            single=parse_bool(row.get("single", "false")),
            interested_in=parse_pipe_list(row.get("interested_in", "")),
            plus_one=plus_one,
            sit_with_partner=sit_with_partner,
            min_known=int(row.get("min_known", 0)),
            min_unknown=int(row.get("min_unknown", 0)),
            weight=int(row.get("weight", 1)),
            must_with=parse_pipe_list(row.get("must_with", "")),
            must_separate=parse_pipe_list(row.get("must_separate", "")),
            groups=parse_pipe_list(row.get("groups", "")),
        )
        guests.append(guest)

    names = {g.name for g in guests}
    for g in guests:
        for other in g.must_with + g.must_separate:
            if other not in names:
                raise ValueError(f"Unknown guest referenced by {g.name}: {other}")
    return guests


def load_tables(path: Path | str | IO[Any]) -> List[Table]:
    """Load table definitions."""
    df = pd.read_csv(path)
    tables: List[Table] = []
    for _, row in df.iterrows():
        tables.append(
            Table(
                name=row["name"],
                capacity=int(row["capacity"]),
                tags=parse_pipe_list(row.get("tags", "")),
            )
        )
    return tables


def load_relationships(path: Path | str | IO[Any], guest_names: set[str] | None = None) -> List[Relationship]:
    """Load relationships between guests.

    If ``guest_names`` is provided it validates that both endpoints exist.
    """
    df = pd.read_csv(path)
    relationships: List[Relationship] = []
    for _, row in df.iterrows():
        a = str(row["guest1_id"]).strip()
        b = str(row["guest2_id"]).strip()
        if guest_names:
            guest_names_stripped = set(str(g).strip() for g in guest_names)
            if a not in guest_names_stripped or b not in guest_names_stripped:
                raise ValueError(f"Relationship references unknown guest: {a}, {b}")
        relationships.append(
            Relationship(
                a=a,
                b=b,
                relation=row.get("relationship", "neutral"),
                strength=int(row.get("strength", 0)),
                notes=row.get("notes", ""),
            )
        )
    return relationships


def load_all(guests_path: Path | str, relationships_path: Path | str, tables_path: Path | str):
    """Convenience wrapper returning guests, relationships and tables."""
    guests = load_guests(guests_path)
    guest_ids = {str(g.id) for g in guests}
    relationships = load_relationships(relationships_path, guest_ids)
    tables = load_tables(tables_path)
    return guests, relationships, tables
