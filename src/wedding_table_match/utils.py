import os
import csv
from pathlib import Path

def generate_sample_wedding_csvs(downloads_dir=None):
    """
    Generates sample guests.csv, relationships.csv, and tables.csv files in the user's Downloads folder.
    Returns a dict with the paths to each file.
    """
    if downloads_dir is None:
        downloads_dir = str(Path.home() / "Downloads")
    os.makedirs(downloads_dir, exist_ok=True)

    guests_path = os.path.join(downloads_dir, "guests.csv")
    relationships_path = os.path.join(downloads_dir, "relationships.csv")
    tables_path = os.path.join(downloads_dir, "tables.csv")

    # Sample data
    guests = [
        ["id", "name"],
        ["1", "Alice"],
        ["2", "Bob"],
        ["3", "Charlie"],
        ["4", "Diana"],
        ["5", "Eve"],
        ["6", "Frank"],
        ["7", "Grace"],
        ["8", "Hank"],
        ["9", "Ivy"],
        ["10", "Jack"],
        ["11", "Karen"],
        ["12", "Leo"],
        ["13", "Mona"],
        ["14", "Nina"],
        ["15", "Oscar"],
        ["16", "Paul"],
        ["17", "Quinn"],
        ["18", "Rita"],
        ["19", "Sam"],
        ["20", "Tina"],
    ]
    relationships = [
        ["guest1_id", "guest2_id", "relationship"],
        ["1", "2", "friends"],
        ["1", "3", "friends"],
        ["2", "4", "conflict"],
        ["3", "5", "friends"],
        ["4", "6", "friends"],
        ["5", "7", "conflict"],
        ["6", "8", "friends"],
        ["7", "9", "friends"],
        ["8", "10", "conflict"],
        ["9", "11", "friends"],
    ]
    tables = [
        ["name", "capacity"],
        ["A", "4"],
        ["B", "4"],
        ["C", "4"],
        ["D", "4"],
        ["E", "4"],
    ]

    # Write CSVs
    with open(guests_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(guests)
    with open(relationships_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(relationships)
    with open(tables_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(tables)

    return {
        "guests": guests_path,
        "relationships": relationships_path,
        "tables": tables_path,
    }

paths = generate_sample_wedding_csvs()
print("Sample CSVs generated:")
for name, path in paths.items():
    print(f"{name}: {path}")


"""
Example usage:

from wedding_table_match.utils import generate_sample_wedding_csvs

paths = generate_sample_wedding_csvs()
print("Sample CSVs generated:")
for name, path in paths.items():
    print(f"{name}: {path}")

python src/wedding_table_match/utils.py
"""
