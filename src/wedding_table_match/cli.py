# /Users/macallansavett/code/WeddingTableMatch/src/wedding_table_match/cli.py
"""Command line interface for WeddingTableMatch."""
from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Sequence

from .csv_loader import load_all
from .solver import SeatingModel, grade_tables, compute_table_stats


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Wedding seating assignment")
    parser.add_argument("--guests", required=True, help="Path to guests.csv")
    parser.add_argument("--relationships", required=True, help="Path to relationships.csv")
    parser.add_argument("--tables", required=True, help="Path to tables.csv")
    parser.add_argument("--group-by-meal-preference", action="store_true",
                        help="Group guests by meal preference when assigning tables.")
    parser.add_argument("--group-singles", action="store_true",
                        help="Try grouping singles into compatible clusters.")
    parser.add_argument("--min-known", type=int, default=0,
                        help="Soft target for minimum known neighbors per guest.")
    parser.add_argument("--maximize-known", action="store_true",
                        help="Bias scoring toward known relationships where data is sparse.")
    parser.add_argument("--out-assignments", type=Path,
                        help="Write assignments CSV: guest,table.")
    parser.add_argument("--out-report", type=Path,
                        help="Write per-table report CSV with scores and grades.")
    return parser


def main(argv: Sequence[str] | None = None) -> None:
    """Entry point used by ``python -m wedding_table_match.cli``."""
    parser = build_parser()
    args = parser.parse_args(argv)

    guests, relationships, tables = load_all(args.guests, args.relationships, args.tables)

    model = SeatingModel(
        maximize_known=args.maximize_known,
        group_singles=args.group_singles,
        min_known=args.min_known,
        group_by_meal_preference=getattr(args, "group_by_meal_preference", False),
    )
    model.build(guests, tables, relationships)
    assignments = model.solve()

    # Print simple assignments
    for guest, table in sorted(assignments.items()):
        print(f"{guest},{table}")

    # Optional outputs
    if args.out_assignments:
        args.out_assignments.parent.mkdir(parents=True, exist_ok=True)
        with args.out_assignments.open("w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["guest", "table"])
            for guest, table in sorted(assignments.items()):
                w.writerow([guest, table])

    # Build and optionally write a per-table report
    table_to_members = {}
    for guest, table in assignments.items():
        table_to_members.setdefault(table, []).append(guest)

    stats = []
    for table in sorted(table_to_members.keys()):
        members = sorted(table_to_members[table])
        s = compute_table_stats(members, model.get_relationship)
        s["table"] = table
        s["members"] = "|".join(members)
        stats.append(s)

    graded = grade_tables(stats)

    # Print a compact table summary
    for s in graded:
        print(f"[REPORT] {s['table']} grade={s['grade']} mean={s['mean_score']:.2f} "
              f"pairs={s['pair_count']} pos={s['pos_pairs']} neg={s['neg_pairs']} neu={s['neu_pairs']}")

    if args.out_report:
        args.out_report.parent.mkdir(parents=True, exist_ok=True)
        with args.out_report.open("w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=[
                "table", "grade", "mean_score", "total_score", "pair_count",
                "pos_pairs", "neg_pairs", "neu_pairs", "members"
            ])
            w.writeheader()
            for s in graded:
                w.writerow({
                    "table": s["table"],
                    "grade": s["grade"],
                    "mean_score": f"{s['mean_score']:.4f}",
                    "total_score": s["total_score"],
                    "pair_count": s["pair_count"],
                    "pos_pairs": s["pos_pairs"],
                    "neg_pairs": s["neg_pairs"],
                    "neu_pairs": s["neu_pairs"],
                    "members": s["members"],
                })


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    main()
