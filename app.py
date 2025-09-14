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

# -------------------------------
# Run button (always visible, but disabled if not ready)
# -------------------------------

guests_df = rel_df = tables_df = None
guests_valid = rel_valid = tables_valid = False
rel_guests_ok = True

run_disabled = True
if _guests_file and _relationships_file and _tables_file:
    # We'll update this after validation below
    run_disabled = False
run_clicked = st.button("Run solver", disabled=run_disabled, key="run_solver_button")

# -------------------------------
# Helpers
# -------------------------------

def validate_columns(df: pd.DataFrame, required: list[str], file_label: str) -> bool:
    missing = [col for col in required if col not in df.columns]
    if missing:
        st.error(f"Error in {file_label}: missing columns: {', '.join(missing)}")
        return False
    return True

def validate_relationship_guests(guests_df: pd.DataFrame, rel_df: pd.DataFrame) -> bool:
    # Force string compare so 1 and "1" match
    guest_ids = set(guests_df["id"].astype(str))
    st.write("[DEBUG] Guest IDs:", sorted(guest_ids))
    rel_ids = set()
    bad_rows = []
    for idx, row in rel_df.iterrows():
        a = str(row["guest1_id"])
        b = str(row["guest2_id"])
        rel_ids.add(a)
        rel_ids.add(b)
        if a not in guest_ids or b not in guest_ids:
            bad_rows.append((idx, a, b))
    st.write("[DEBUG] Relationship referenced IDs:", sorted(rel_ids))
    if bad_rows:
        st.error(
            "Error: The following relationships reference unknown guest IDs: "
            + ", ".join([f"row {i+2}: {a}, {b}" for i, a, b in bad_rows])
            + ". Please check your guests and relationships files."
        )
        return False
    return True


# -------------------------------
# Preview uploaded data with validation
# -------------------------------

guests_df = rel_df = tables_df = None
guests_valid = rel_valid = tables_valid = False
rel_guests_ok = True

if _guests_file is not None:
    guests_df = pd.read_csv(_guests_file)
    # Normalize id to string for consistent validation
    if "id" in guests_df.columns:
        guests_df["id"] = guests_df["id"].astype(str)
    st.subheader("Guests preview")
    st.dataframe(guests_df)
    guests_valid = validate_columns(guests_df, ["id", "name"], "guests.csv")

if _relationships_file is not None:
    rel_df = pd.read_csv(_relationships_file)
    # Normalize id fields to string
    for c in ("guest1_id", "guest2_id"):
        if c in rel_df.columns:
            rel_df[c] = rel_df[c].astype(str)
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

# -------------------------------
# Run button (always visible, but disabled if not ready)
# -------------------------------

run_disabled = not (_guests_file and _relationships_file and _tables_file and guests_valid and rel_valid and tables_valid and rel_guests_ok)

# -------------------------------
# Solve when all files are valid and button pressed
# -------------------------------

if run_clicked and not run_disabled:
    # Reset file pointers before re-reading
    _guests_file.seek(0)
    _relationships_file.seek(0)
    _tables_file.seek(0)

    try:
        guests = load_guests(_guests_file)
        tables = load_tables(_tables_file)

        # Pass guest IDs, not names. Normalize to string for safety.
        valid_ids = {str(getattr(g, "id")) for g in guests}
        relationships = load_relationships(_relationships_file, valid_ids)

        model = SeatingModel()
        model.build(guests, tables, relationships)
        assignments = model.solve()

    except ValueError as e:
        st.error(f"Input validation error: {e}")
        st.stop()
    except Exception as e:
        st.exception(e)
        st.stop()

    result_df = (
        pd.DataFrame(
            {"guest": list(assignments.keys()), "table": list(assignments.values())}
        )
        .sort_values("table")
        .reset_index(drop=True)
    )
    st.subheader("Assignments")
    st.dataframe(result_df)

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
