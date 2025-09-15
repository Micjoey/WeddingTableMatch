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
        ["id", "name", "age", "gender", "gender_identity", "rsvp", "meal_preference", "plus_one", "sit_with_partner", "single", "interested_in"],
        ["1", "Alice", "28", "F", "F", "yes", "vegetarian", "true", "true", "false", "M"],
        ["2", "Bob", "32", "M", "M", "yes", "chicken", "false", "true", "true", "F"],
        ["3", "Charlie", "35", "M", "M", "no", "beef", "false", "true", "false", "F"],
        ["4", "Diana", "30", "F", "F", "yes", "fish", "true", "true", "true", "M"],
        ["5", "Eve", "27", "F", "F", "yes", "vegetarian", "false", "true", "false", "M"],
        ["6", "Frank", "40", "M", "M", "no", "chicken", "false", "true", "false", "F"],
        ["7", "Grace", "29", "F", "F", "yes", "beef", "true", "true", "true", "F|M"],
        ["8", "Hank", "33", "M", "M", "yes", "fish", "false", "true", "false", "F"],
        ["9", "Ivy", "26", "F", "F", "yes", "vegetarian", "false", "true", "false", "M"],
        ["10", "Jack", "31", "M", "M", "yes", "chicken", "true", "true", "true", "F"],
        ["11", "Karen", "34", "F", "F", "no", "beef", "false", "true", "false", "M"],
        ["12", "Leo", "38", "M", "M", "yes", "fish", "false", "true", "false", "F"],
        ["13", "Mona", "25", "F", "F", "yes", "vegetarian", "true", "true", "false", "M"],
        ["14", "Nina", "29", "F", "F", "yes", "chicken", "false", "true", "true", "F"],
        ["15", "Oscar", "36", "M", "M", "no", "beef", "false", "true", "false", "F"],
        ["16", "Paul", "37", "M", "M", "yes", "fish", "true", "true", "false", "F"],
        ["17", "Quinn", "28", "F", "F", "yes", "vegetarian", "false", "true", "false", "M"],
        ["18", "Rita", "32", "F", "F", "yes", "chicken", "false", "true", "true", "M"],
        ["19", "Sam", "35", "M", "M", "no", "beef", "false", "true", "false", "F"],
        ["20", "Tina", "30", "F", "F", "yes", "fish", "true", "true", "false", "M"],
    ]
    relationships = [
        ["guest1_id", "guest2_id", "relationship"],
        ["1", "2", "friend"],
        ["1", "3", "friend"],
        ["2", "4", "conflict"],
        ["3", "5", "friend"],
        ["4", "6", "friend"],
        ["5", "7", "conflict"],
        ["6", "8", "friend"],
        ["7", "9", "friend"],
        ["8", "10", "conflict"],
        ["9", "11", "friend"],
        ["1", "4", "best friend"],
        ["2", "3", "avoid"],
        ["5", "6", "neutral"],
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

# Relationship scale for table grading:
#   best friend: +5
#   friend: +3
#   know: +2
#   neutral: 0
#   avoid: -3
#   conflict: -5
# Table compatibility is graded A–F based on the average relationship score among all pairs at the table.

# Run with:
# python src/wedding_table_match/utils.py
"""
