import pathlib
import sys

# Ensure src package is on path
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from wedding_table_match import csv_loader, solver


def test_full_flow():
    data_dir = pathlib.Path(__file__).parent / "data"
    guests, relationships, tables = csv_loader.load_all(
        data_dir / "guests.csv", data_dir / "relationships.csv", data_dir / "tables.csv"
    )

    model = solver.SeatingModel()
    model.build(guests, tables, relationships)
    assignments = model.solve()

    # all guests assigned
    assert len(assignments) == len(guests)

    # table capacities respected
    counts = {}
    for table_name in assignments.values():
        counts[table_name] = counts.get(table_name, 0) + 1
    for t in tables:
        assert counts.get(t.name, 0) <= t.capacity
