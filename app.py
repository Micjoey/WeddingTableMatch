"""Streamlit UI for WeddingTableMatch with CSV previews and validations."""
from __future__ import annotations

# Add src to sys.path so wedding_table_match can be found
import sys
import os
import io
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from wedding_table_match.csv_loader import (
    load_guests,
    load_relationships,
    load_tables,
)
from wedding_table_match.models import Table
from wedding_table_match.solver import SeatingModel

# -----------------------------
# Helpers
# -----------------------------

def uploadedfile_to_df(uploaded_file) -> pd.DataFrame | None:
    """Read a Streamlit UploadedFile or file-like object into a DataFrame."""
    if uploaded_file is None:
        return None
    if hasattr(uploaded_file, "read"):
        uploaded_file.seek(0)
        return pd.read_csv(io.StringIO(uploaded_file.read().decode("utf-8")))
    return pd.read_csv(uploaded_file)

def df_to_csvio(df: pd.DataFrame) -> io.StringIO:
    """Serialize a DataFrame to a StringIO CSV buffer positioned at start."""
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    buf.seek(0)
    return buf

def validate_columns(df: pd.DataFrame, required: list[str], file_label: str) -> bool:
    """Check required columns and show an error if any are missing."""
    missing = [col for col in required if col not in df.columns]
    if missing:
        st.error(f"Error in {file_label}: missing columns: {', '.join(missing)}")
        return False
    return True

def validate_relationship_guests(guests_df: pd.DataFrame, rel_df: pd.DataFrame) -> bool:
    """Ensure relationship guest ids exist in guests."""
    guest_ids = set(guests_df["id"].astype(str))
    bad_rows = []
    for idx, row in rel_df.iterrows():
        a = str(row["guest1_id"])
        b = str(row["guest2_id"])
        if a not in guest_ids or b not in guest_ids:
            bad_rows.append((idx, a, b))
    if bad_rows:
        st.error(
            "Error: relationships reference unknown guest ids: "
            + ", ".join([f"row {i+2}: {a}, {b}" for i, a, b in bad_rows])
            + ". Fix guests.csv or relationships.csv."
        )
        return False
    return True

def build_and_solve(
    guests_df: pd.DataFrame,
    tables_df: pd.DataFrame,
    rel_df: pd.DataFrame,
    single_table: bool,
    maximize_known: bool,
    group_singles: bool,
    min_known: int,
):
    """Run loaders, build model, and solve assignments."""
    # Convert DFs to CSV buffers for existing loaders
    guests_csv = df_to_csvio(guests_df)
    tables_csv = df_to_csvio(tables_df)
    rel_csv = df_to_csvio(rel_df)

    guests = load_guests(guests_csv)
    tables = load_tables(tables_csv)

    # Pass guest ids to relationship loader
    valid_ids = {str(getattr(g, "id")) for g in guests}
    relationships = load_relationships(rel_csv, valid_ids)

    if single_table:
        total_capacity = sum(t.capacity for t in tables)
        if len(guests) > total_capacity:
            raise ValueError("Not enough total capacity for a single table.")
        tables = [Table(name="All", capacity=len(guests), tags=[])]

    model = SeatingModel(
        maximize_known=maximize_known,
        group_singles=group_singles,
        min_known=min_known,
    )
    model.build(guests, tables, relationships)
    return guests, relationships, model.solve()

# -----------------------------
# Sidebar options
# -----------------------------

st.sidebar.header("Seating Options")
maximize_known = st.sidebar.checkbox(
    "Maximize known guests per table",
    value=False,
    help="Try to seat more people who know each other at the same table.",
)
min_known = st.sidebar.number_input(
    "Minimum known people per guest at table",
    min_value=0,
    max_value=20,
    value=0,
    help="Try to ensure each guest has at least this many known people at their table.",
)
single_table = st.sidebar.checkbox(
    "Force all guests at one table",
    value=False,
    help="Assign everyone to a single table if capacity allows.",
)
group_singles = st.sidebar.checkbox(
    "Group single guests together",
    value=False,
    help="Try to seat single guests at the same table if possible.",
)
group_by_meal_preference = st.sidebar.checkbox(
    "Group guests by meal preference",
    value=False,
    help="Try to seat guests with the same meal preference together if possible."
)

# -----------------------------
# Main UI and previews
# -----------------------------

st.title("Wedding Table Match")

_guests_file = st.file_uploader("Guests CSV", type="csv")
_relationships_file = st.file_uploader("Relationships CSV", type="csv")
_tables_file = st.file_uploader("Tables CSV", type="csv")

guests_df = rel_df = tables_df = None
guests_valid = rel_valid = tables_valid = False
rel_guests_ok = True

# Guests preview and column check
if _guests_file is not None:
    guests_df = pd.read_csv(_guests_file)
    # Normalize id to string for consistent checks
    if "id" in guests_df.columns:
        guests_df["id"] = guests_df["id"].astype(str)
    st.subheader("Guests preview")
    st.dataframe(guests_df, use_container_width=True)
    guests_valid = validate_columns(guests_df, ["id", "name"], "guests.csv")
    _guests_file.seek(0)

# Relationships preview and column check
if _relationships_file is not None:
    rel_df = pd.read_csv(_relationships_file)
    # Normalize id fields to string
    for c in ("guest1_id", "guest2_id"):
        if c in rel_df.columns:
            rel_df[c] = rel_df[c].astype(str)
    st.subheader("Relationships preview")
    st.dataframe(rel_df, use_container_width=True)
    rel_valid = validate_columns(rel_df, ["guest1_id", "guest2_id", "relationship"], "relationships.csv")
    _relationships_file.seek(0)

# Tables preview and column check
if _tables_file is not None:
    tables_df = pd.read_csv(_tables_file)
    st.subheader("Tables preview")
    st.dataframe(tables_df, use_container_width=True)
    tables_valid = validate_columns(tables_df, ["name", "capacity"], "tables.csv")
    _tables_file.seek(0)

# Cross validate relationships vs guests as soon as both are present and valid
if guests_df is not None and rel_df is not None and guests_valid and rel_valid:
    rel_guests_ok = validate_relationship_guests(guests_df, rel_df)

# -----------------------------
# Run button
# -----------------------------

# Keep the button disabled until all files are provided
run_disabled = not (_guests_file and _relationships_file and _tables_file)
run_clicked = st.button("Run solver", disabled=run_disabled, key="run_solver_button")

# -----------------------------
# Solve
# -----------------------------

if run_clicked and not run_disabled:
    try:
        # Re-read uploads into DataFrames for the solver path
        guests_df_run = uploadedfile_to_df(_guests_file)
        tables_df_run = uploadedfile_to_df(_tables_file)
        rel_df_run = uploadedfile_to_df(_relationships_file)

        if guests_df_run is None or tables_df_run is None or rel_df_run is None:
            st.error("One or more input files could not be read. Please upload valid CSV files.")
            st.stop()
            group_by_meal_preference=group_by_meal_preference,

        # Normalize ids for validation parity
        if "id" in guests_df_run.columns:
            guests_df_run["id"] = guests_df_run["id"].astype(str)
        for c in ("guest1_id", "guest2_id"):
            if c in rel_df_run.columns:
                rel_df_run[c] = rel_df_run[c].astype(str)

        # Validate again before solving
        if not validate_columns(guests_df_run, ["id", "name"], "guests.csv"):
            st.stop()
        if not validate_columns(rel_df_run, ["guest1_id", "guest2_id", "relationship"], "relationships.csv"):
            st.stop()
        if not validate_columns(tables_df_run, ["name", "capacity"], "tables.csv"):
            st.stop()
        if not validate_relationship_guests(guests_df_run, rel_df_run):
            st.stop()

        # Solve
        guests, relationships, assignments = build_and_solve(
            guests_df_run,
            tables_df_run,
            rel_df_run,
            single_table=single_table,
            maximize_known=maximize_known,
            group_singles=group_singles,
            min_known=min_known,
        )

        # Results table
        result_df = (
            pd.DataFrame(
                {"guest": list(assignments.keys()), "table": list(assignments.values())}
            )
            .sort_values("table")
            .reset_index(drop=True)
        )
        st.subheader("Assignments")
        st.dataframe(result_df, use_container_width=True)

        # Grouped summary per table
        grouped_df = (
            result_df.groupby("table")["guest"]
            .apply(lambda g: ", ".join(g))
            .reset_index(name="guests")
        )
        st.subheader("Guests per table")
        st.dataframe(grouped_df, use_container_width=True)

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
