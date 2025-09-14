"""Streamlit UI for WeddingTableMatch."""
from __future__ import annotations

# Add src to sys.path so wedding_table_match can be found
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

import pandas as pd
import streamlit as st
import networkx as nx
from pyvis.network import Network
import streamlit.components.v1 as components

from wedding_table_match.csv_loader import (
    load_guests,
    load_relationships,
    load_tables,
)
from wedding_table_match.models import Table
from wedding_table_match.solver import SeatingModel


st.title("Wedding Table Match")

# --- User Options ---
st.sidebar.header("Seating Options")

maximize_known = st.sidebar.checkbox("Maximize known guests per table", value=False, help="Try to seat more people who know each other at the same table.")
min_known = st.sidebar.number_input(
    "Minimum known people per guest at table",
    min_value=0,
    max_value=20,
    value=0,
    help="Try to ensure each guest has at least this many people they know at their table (if possible)."
)
single_table = st.sidebar.checkbox("Force all guests at one table", value=False, help="Assign everyone to a single table (if capacity allows).")
group_singles = st.sidebar.checkbox("Group single guests together", value=False, help="Try to seat single guests at the same table(s) if possible.")


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
    rel_ids = set()
    bad_rows = []
    for idx, row in rel_df.iterrows():
        a = str(row["guest1_id"])
        b = str(row["guest2_id"])
        rel_ids.add(a)
        rel_ids.add(b)
        if a not in guest_ids or b not in guest_ids:
            bad_rows.append((idx, a, b))
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

        # Optionally modify tables/guests based on user options
        if single_table:
            # Collapse all tables into one big table (if possible)
            total_capacity = sum(t.capacity for t in tables)
            if len(guests) > total_capacity:
                raise ValueError("Not enough total capacity for all guests at one table.")
            tables = [Table(name="All", capacity=len(guests), tags=[])]
    model = SeatingModel(maximize_known=maximize_known, group_singles=group_singles, min_known=min_known)
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

    # --- Mind Map Visualization ---
    st.subheader("Assignment Mind Map")
    from generate_assignment_mind_map import generate_assignment_mind_map
    html = generate_assignment_mind_map(assignments, guests, relationships)
    components.html(html, height=600, scrolling=True)
