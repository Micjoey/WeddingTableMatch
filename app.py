"""Streamlit UI for WeddingTableMatch."""
from __future__ import annotations

# Add src to sys.path so wedding_table_match can be found
import sys
import os
import io
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

# Restore import block
from wedding_table_match.csv_loader import (
    load_guests,
    load_relationships,
    load_tables,
)
from wedding_table_match.models import Table
from wedding_table_match.solver import SeatingModel

# -----------------------------
# Sidebar: user options
# -----------------------------
st.sidebar.header("Seating Options")
maximize_known = st.sidebar.checkbox(
    "Maximize known guests per table",
    value=False,
    help="Try to seat more people who know each other at the same table."
)
min_known = st.sidebar.number_input(
    "Minimum known people per guest at table",
    min_value=0,
    max_value=20,
    value=0,
    help="Try to ensure each guest has at least this many people they know at their table if possible."
)
single_table = st.sidebar.checkbox(
    "Force all guests at one table",
    value=False,
    help="Assign everyone to a single table if capacity allows."
)
group_singles = st.sidebar.checkbox(
    "Group single guests together",
    value=False,
    help="Try to seat single guests at the same table or tables if possible."
)

# -----------------------------
# Main controls
# -----------------------------
st.title("Wedding Table Match")

_guests_file = st.file_uploader("Guests CSV", type="csv")
_relationships_file = st.file_uploader("Relationships CSV", type="csv")
_tables_file = st.file_uploader("Tables CSV", type="csv")

def uploadedfile_to_df(uploaded_file):
    """Load a Streamlit UploadedFile or file-like object into a DataFrame."""
    if uploaded_file is None:
        return None
    if hasattr(uploaded_file, "read"):
        uploaded_file.seek(0)
        return pd.read_csv(io.StringIO(uploaded_file.read().decode("utf-8")))
    return pd.read_csv(uploaded_file)

# Enable the button only when all files are present
run_disabled = not (_guests_file and _relationships_file and _tables_file)
run_clicked = st.button("Run solver", disabled=run_disabled, key="run_solver_button")

# -----------------------------
# Run flow
# -----------------------------
if run_clicked and not run_disabled:
    try:
        # Load DataFrames from uploads
        guests_df = uploadedfile_to_df(_guests_file)
        tables_df = uploadedfile_to_df(_tables_file)
        rel_df = uploadedfile_to_df(_relationships_file)

        if guests_df is None or tables_df is None or rel_df is None:
            st.error("One or more input files could not be read. Please upload valid CSV files.")
            st.stop()

        # Convert DFs to in-memory CSVs for the existing loaders
        guests_csv = io.StringIO()
        tables_csv = io.StringIO()
        rel_csv = io.StringIO()

        guests_df.to_csv(guests_csv, index=False); guests_csv.seek(0)
        tables_df.to_csv(tables_csv, index=False); tables_csv.seek(0)
        rel_df.to_csv(rel_csv, index=False); rel_csv.seek(0)

        # Use loaders
        guests = load_guests(guests_csv)
        tables = load_tables(tables_csv)

        # Pass guest IDs, not names. Normalize to string for safety.
        valid_ids = {str(getattr(g, "id")) for g in guests}
        relationships = load_relationships(rel_csv, valid_ids)

        # Optional: consolidate to a single table if requested and capacity allows
        if single_table:
            total_capacity = sum(t.capacity for t in tables)
            if len(guests) > total_capacity:
                raise ValueError("Not enough total capacity for all guests at one table.")
            tables = [Table(name="All", capacity=len(guests), tags=[])]

        # Build and solve
        model = SeatingModel(
            maximize_known=maximize_known,
            group_singles=group_singles,
            min_known=min_known,
        )
        model.build(guests, tables, relationships)
        assignments = model.solve()

        # Results table
        result_df = (
            pd.DataFrame(
                {"guest": list(assignments.keys()), "table": list(assignments.values())}
            )
            .sort_values("table")
            .reset_index(drop=True)
        )
        st.subheader("Assignments")
        st.dataframe(result_df)

        # Grouped summary per table
        grouped_df = (
            result_df.groupby("table")["guest"]
            .apply(lambda g: ", ".join(g))
            .reset_index(name="guests")
        )
        st.subheader("Guests per table")
        st.dataframe(grouped_df)

        # Download
        csv_bytes = result_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Download assignments as CSV",
            csv_bytes,
            file_name="assignments.csv",
        )

        # Mind map visualization
        st.subheader("Assignment Mind Map")
        from generate_assignment_mind_map import generate_assignment_mind_map
        html = generate_assignment_mind_map(assignments, guests, relationships)
        components.html(html, height=600, scrolling=True)

    except ValueError as e:
        st.error(f"Input validation error: {e}")
        st.stop()
    except Exception as e:
        st.exception(e)
        st.stop()
