"""Utility functions for WeddingTableMatch.

Sample CSV generators and seating option definitions for the sidebar UI.
"""

import csv
from pathlib import Path


def write_sample_guests_csv(path: str | Path):
    """Write a sample guests CSV including all supported fields."""
    header = [
        "id", "name", "age", "gender_identity", "rsvp", "meal_preference",
        "single", "interested_in", "plus_one", "sit_with_partner", "min_known",
        "min_unknown", "weight", "must_with", "must_separate", "groups",
        "hobbies", "languages", "relationship_status", "forced_table",
        "location", "diet_choices", "partner",
    ]
    rows = [
        [1, "Alice", 29, "Female", "Yes", "Vegetarian", True, "reading|hiking", False, True, 1, 0, 1, "Bob", "", "Friends", "reading|yoga", "English|Spanish", "single", "", "New York", "vegetarian|gluten-free", 2],
        [2, "Bob", 31, "Male", "Yes", "Chicken", False, "reading|sports", False, True, 1, 0, 1, "Alice", "", "Friends", "reading|yoga", "English", "single", "", "New York", "none", 1],
        [3, "Carol", 27, "Female", "Yes", "Fish", True, "travel|music", False, True, 1, 0, 1, "", "", "Family", "music|travel", "French|English", "single", "Table 2", "Paris", "vegan", ""],
        [4, "David", 35, "Male", "Yes", "Beef", False, "golf|cooking", False, True, 1, 0, 1, "", "", "Work", "golf|cooking", "English|German", "married", "", "Berlin", "none", 5],
        [5, "Eve", 28, "Female", "Yes", "Vegetarian", True, "reading|music", False, True, 1, 0, 1, "", "", "Friends", "reading|music", "English", "single", "", "New York", "vegetarian", 4],
    ]
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)


def write_sample_relationships_csv(path: str | Path):
    """Write a sample relationships CSV."""
    header = ["guest1_id", "guest2_id", "relationship", "strength", "notes"]
    rows = [
        [1, 2, "friend", 3, "Alice and Bob are friends"],
        [1, 3, "know", 2, "Alice knows Carol"],
        [2, 3, "neutral", 0, "Bob and Carol are neutral"],
        [4, 5, "married", 5, "David and Eve are married"],
    ]
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)


def write_sample_tables_csv(path: str | Path):
    """Write a sample tables CSV."""
    header = ["name", "capacity", "tags"]
    rows = [
        ["Table 1", 3, "Friends"],
        ["Table 2", 3, "Family"],
    ]
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)


# Seating option definitions for sidebar UI
SEATING_OPTIONS = {
    "maximize_known": {
        "label": "Maximize Known Relationships",
        "type": "toggle",
        "default": False,
        "description": "Bias scoring toward positive relationships where data is sparse.",
    },
    "group_singles": {
        "label": "Group Singles",
        "type": "toggle",
        "default": False,
        "description": "Try grouping singles into compatible clusters.",
    },
    "min_known": {
        "label": "Minimum Known Neighbors",
        "type": "number",
        "default": 0,
        "description": "Soft target for minimum known neighbors per guest.",
    },
    "group_by_meal_preference": {
        "label": "Group by Meal Preference",
        "type": "toggle",
        "default": False,
        "description": "Group guests by meal preference when assigning tables.",
    },
    "balance_tables": {
        "label": "Equalize Table Sizes",
        "type": "toggle",
        "default": False,
        "description": "Strongly encourage near-equal table sizes.",
    },
    "balance_weight": {
        "label": "Table Size Balance Strength",
        "type": "number",
        "default": 8.0,
        "description": "Strength of size balancing. Larger is stronger.",
    },
    "match_hobbies": {
        "label": "Match by Hobbies",
        "type": "toggle",
        "default": False,
        "description": "Encourage seating guests with shared hobbies.",
    },
    "match_languages": {
        "label": "Match by Languages",
        "type": "toggle",
        "default": False,
        "description": "Encourage seating guests with shared languages.",
    },
    "match_age": {
        "label": "Match by Age Range",
        "type": "toggle",
        "default": False,
        "description": "Encourage seating guests within similar age ranges.",
    },
    "match_relationship_status": {
        "label": "Match by Relationship Status",
        "type": "toggle",
        "default": False,
        "description": "Encourage seating guests with the same relationship status.",
    },
    "match_location": {
        "label": "Match by Location",
        "type": "toggle",
        "default": False,
        "description": "Encourage seating guests from the same location.",
    },
    "match_diet": {
        "label": "Match by Diet Choices",
        "type": "toggle",
        "default": False,
        "description": "Encourage seating guests with similar diet choices.",
    },
    "respect_forced_table": {
        "label": "Respect Forced Table Assignments",
        "type": "toggle",
        "default": False,
        "description": "Force guests to assigned tables if specified.",
    },
    "layout": {
        "label": "Mind Map Layout",
        "type": "select",
        "default": "round",
        "choices": ["round", "square", "rectangle"],
        "description": "Choose the shape for the seating mind map visualization.",
    },
}


def get_seating_options() -> dict:
    """Return the seating options dictionary for sidebar UI."""
    return SEATING_OPTIONS


if __name__ == "__main__":
    import os

    guests_path = os.path.abspath("guests_sample.csv")
    relationships_path = os.path.abspath("relationships_sample.csv")
    tables_path = os.path.abspath("tables_sample.csv")
    print(f"Writing sample CSVs:\n  {guests_path}\n  {relationships_path}\n  {tables_path}")
    write_sample_guests_csv(guests_path)
    write_sample_relationships_csv(relationships_path)
    write_sample_tables_csv(tables_path)
    print("Done.")
