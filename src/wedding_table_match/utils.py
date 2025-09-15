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
    import random
    first_names = [
        "Alice", "Bob", "Charlie", "Diana", "Eve", "Frank", "Grace", "Hank", "Ivy", "Jack",
        "Karen", "Leo", "Mona", "Nina", "Oscar", "Paul", "Quinn", "Rita", "Sam", "Tina",
        "Uma", "Victor", "Wendy", "Xander", "Yara", "Zane", "Amy", "Ben", "Cara", "Dan",
        "Ella", "Finn", "Gina", "Hugo", "Isla", "Jon", "Kira", "Liam", "Mia", "Noah",
        "Olga", "Pete", "Queenie", "Rob", "Sara", "Tom", "Ursula", "Vince", "Will", "Xena",
        "Yuri", "Zoe", "Ava", "Blake", "Cleo", "Derek", "Elsa", "Felix", "Gwen", "Harvey",
        "Iris", "Jude", "Kara", "Lars", "Mila", "Nico", "Omar", "Pia", "Quentin", "Rosa",
        "Seth", "Tara", "Ulric", "Vera", "Walt", "Ximena", "Yosef", "Zelda"
    ]
    genders = ["M", "F"]
    meal_prefs = ["chicken", "beef", "fish", "vegetarian", "vegan"]
    guests = [["id", "name", "age", "gender", "gender_identity", "rsvp", "meal_preference", "plus_one", "sit_with_partner", "single", "interested_in"]]
    for i in range(80):
        name = first_names[i % len(first_names)]
        gender = genders[i % 2]
        age = random.randint(21, 65)
        rsvp = "yes" if random.random() > 0.05 else "no"
        meal = random.choice(meal_prefs)
        # About 1/3 singles, 1/3 couples, 1/3 with plus_one
        if i % 6 == 0:
            plus_one = "false"
            sit_with_partner = "false"
            single = "true"
            interested_in = "M|F"
        elif i % 6 in (1, 2):
            plus_one = "true"
            sit_with_partner = "true"
            single = "false"
            interested_in = "F" if gender == "M" else "M"
        else:
            plus_one = "false"
            sit_with_partner = "false"
            single = "false"
            interested_in = "F|M"
        guests.append([
            str(i+1), name, str(age), gender, gender, rsvp, meal, plus_one, sit_with_partner, single, interested_in
        ])

    # Generate dense, varied relationships
    relationships = [["guest1_id", "guest2_id", "relationship"]]
    rel_types = ["best friend"]*2 + ["friend"]*4 + ["know"]*8 + ["avoid"]*2 + ["conflict"]*2 + ["neutral"]*2
    for i in range(1, 81):
        # Each guest has 10-15 relationships
        rel_ids = random.sample([j for j in range(1, 81) if j != i], random.randint(10, 15))
        for j in rel_ids:
            rel = random.choice(rel_types)
            relationships.append([str(i), str(j), rel])

    # 12 tables of 8 (96 seats for 80 guests)
    tables = [["name", "capacity"]]
    for t in range(12):
        tables.append([chr(65+t), "8"])

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
