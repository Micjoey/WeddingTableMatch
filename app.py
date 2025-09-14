
"""Streamlit UI for WeddingTableMatch."""
from __future__ import annotations

# Add src to sys.path so wedding_table_match can be found
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

import pandas as pd
import streamlit as st

from wedding_table_match.csv_loader import (
    load_guests,
    load_relationships,
    load_tables,
)
from wedding_table_match.solver import SeatingModel

st.title("Wedding Table Match")

# File uploaders
_guests_file = st.file_uploader("Guests CSV", type="csv")
_relationships_file = st.file_uploader("Relationships CSV", type="csv")
_tables_file = st.file_uploader("Tables CSV", type="csv")


# File validation helpers

def validate_columns(df, required, file_label):
    missing = [col for col in required if col not in df.columns]
    if missing:
        st.error(f"Error in {file_label}: missing columns: {', '.join(missing)}")
        return False
    return True

def validate_relationship_guests(guests_df, rel_df):
    guest_ids = set(str(x) for x in guests_df["id"].astype(str))
    bad_rows = []
    for idx, row in rel_df.iterrows():
        a = str(row["guest1_id"])
        b = str(row["guest2_id"])
        if a not in guest_ids or b not in guest_ids:
            bad_rows.append((idx, a, b))
    if bad_rows:
        st.error(
            "Error: The following relationships reference unknown guest IDs: " +
            ", ".join([f"row {i+2}: {a}, {b}" for i, a, b in bad_rows]) +
            ". Please check your guests and relationships files."
        )
        return False
    return True


# Preview uploaded data with validation
guests_df = rel_df = tables_df = None
guests_valid = rel_valid = tables_valid = False
rel_guests_ok = True

if _guests_file is not None:
    guests_df = pd.read_csv(_guests_file)
    st.subheader("Guests preview")
    st.dataframe(guests_df)
    guests_valid = validate_columns(guests_df, ["id", "name"], "guests.csv")
if _relationships_file is not None:
    rel_df = pd.read_csv(_relationships_file)
    st.subheader("Relationships preview")
    st.dataframe(rel_df)
    rel_valid = validate_columns(rel_df, ["guest1_id", "guest2_id", "relationship"], "relationships.csv")
if _tables_file is not None:
    tables_df = pd.read_csv(_tables_file)
    st.subheader("Tables preview")
    st.dataframe(tables_df)
    tables_valid = validate_columns(tables_df, ["name", "capacity"], "tables.csv")

# Validate relationships reference only valid guests as soon as both files are uploaded and valid
if guests_df is not None and rel_df is not None and guests_valid and rel_valid:
    rel_guests_ok = validate_relationship_guests(guests_df, rel_df)

# Solve when all files are valid and button pressed

# Only allow running if all files are valid and relationships reference valid guests
if _guests_file and _relationships_file and _tables_file and guests_valid and rel_valid and tables_valid and rel_guests_ok:
    if st.button("Run solver"):
        # Reset file pointers before re-reading
        _guests_file.seek(0)
        _relationships_file.seek(0)
        _tables_file.seek(0)

        guests = load_guests(_guests_file)
        tables = load_tables(_tables_file)
        relationships = load_relationships(
            _relationships_file, {g.name for g in guests}
        )

        model = SeatingModel()
        model.build(guests, tables, relationships)
        assignments = model.solve()

        result_df = (
            pd.DataFrame(
                {"guest": list(assignments.keys()), "table": list(assignments.values())}
            )
            .sort_values("table")
            .reset_index(drop=True)
        )
        st.subheader("Assignments")
        st.dataframe(result_df)

        # Display a grouped summary so each table's guests are easy to read
        grouped_df = (
            result_df.groupby("table")["guest"]
            .apply(lambda g: ", ".join(g))
            .reset_index(name="guests")
        )
        st.subheader("Guests per table")
        st.dataframe(grouped_df)

        csv_bytes = result_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Download assignments as CSV", csv_bytes, file_name="assignments.csv"
        )
