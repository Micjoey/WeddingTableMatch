"""Command line interface for WeddingTableMatch."""
from __future__ import annotations

import argparse
from typing import Sequence

from .csv_loader import load_all
from .solver import SeatingModel


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Wedding seating assignment")
    parser.add_argument("--guests", required=True, help="Path to guests.csv")
    parser.add_argument(
        "--relationships", required=True, help="Path to relationships.csv"
    )
    parser.add_argument("--tables", required=True, help="Path to tables.csv")
    return parser


def main(argv: Sequence[str] | None = None) -> None:
    """Entry point used by ``python -m wedding_table_match.cli``."""
    parser = build_parser()
    args = parser.parse_args(argv)

    guests, relationships, tables = load_all(
        args.guests, args.relationships, args.tables
    )
    model = SeatingModel()
    model.build(guests, tables, relationships)
    assignments = model.solve()

    for guest, table in assignments.items():
        print(f"{guest},{table}")


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    main()
