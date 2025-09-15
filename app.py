"""Streamlit UI for WeddingTableMatch with CSV previews and validations."""
from __future__ import annotations

def compute_table_score_and_singles(guest_names, guests, relationships):
    # Build lookup for guest id/name to guest object
    guest_dict = {str(g.id): g for g in guests}
    name_to_id = {g.name: str(g.id) for g in guests}
    # Build relationship lookup (a,b) -> numeric score
    rel_map = {}
    rel_type_map = {}
    relation_scale = {
        'best friend': 5,
        'friend': 3,
        'know': 2,
        'neutral': 0,
        'avoid': -3,
        'conflict': -5,
    }
    for rel in relationships:
        a, b = str(rel.a), str(rel.b)
        rel_type = getattr(rel, 'relation', '')
        rel_type_map[(a, b)] = rel_type
        rel_type_map[(b, a)] = rel_type
        score = relation_scale.get(rel_type, getattr(rel, 'strength', 0))
        rel_map[(a, b)] = score
        rel_map[(b, a)] = score
    # Get all pairs
    ids = [name_to_id.get(name, name) for name in guest_names]
    n = len(ids)
    if n < 2:
        return 1.0, 0, []  # trivially perfect, 0 singles, no conflicts
    total = 0
    max_total = 0
    # has_conflict variable removed (was unused)
    for i in range(n):
        for j in range(i+1, n):
            s = rel_map.get((ids[i], ids[j]), 0)
            rel_type = rel_type_map.get((ids[i], ids[j]), '')
            # if rel_type in ('conflict', 'avoid'):
            #     has_conflict = True
            total += s
            max_total += 5  # max possible is both are best friends
    # Count singles
    single_count = 0
    for name in guest_names:
        gid = name_to_id.get(name, name)
        if gid is None:
            continue
        guest = guest_dict.get(str(gid))
        if guest and getattr(guest, 'single', False):
            single_count += 1
    # Score can be negative, so scale to 0-1 for percent
    # Always return a tuple with three elements, third is a list of conflicts (empty if none)
    percent = (total / max_total) if max_total > 0 else 1.0
    return percent, single_count, []
import sys
import os
import io
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from wedding_table_match.csv_loader import load_guests, load_tables, load_relationships
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
    # single_table: bool,  # Removed
    maximize_known: bool,
    group_singles: bool,
    min_known: int,
    group_by_meal_preference: bool = False,
    meal_preference_groups: list[str] | None = None,
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

    # Removed single_table logic

    model = SeatingModel(
        maximize_known=maximize_known,
        group_singles=group_singles,
        min_known=min_known,
        group_by_meal_preference=group_by_meal_preference,
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
    value=2,
    help="Try to ensure each guest has at least this many known people at their table.",
)
group_singles = st.sidebar.checkbox(
    "Group single guests together",
    value=True,
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

# For testing: auto-set CSVs from local paths
import io
_guests_file = open("/Users/macallansavett/Downloads/guests.csv", "rb")
_relationships_file = open("/Users/macallansavett/Downloads/relationships.csv", "rb")
_tables_file = open("/Users/macallansavett/Downloads/tables.csv", "rb")
# If you want to use the uploaders, comment out the above and uncomment below:
# _guests_file = st.file_uploader("Guests CSV", type="csv")
# _relationships_file = st.file_uploader("Relationships CSV", type="csv")
# _tables_file = st.file_uploader("Tables CSV", type="csv")

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
    st.dataframe(guests_df, width='stretch')
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
    st.dataframe(rel_df, width='stretch')
    rel_valid = validate_columns(rel_df, ["guest1_id", "guest2_id", "relationship"], "relationships.csv")
    _relationships_file.seek(0)

# Tables preview and column check
if _tables_file is not None:
    tables_df = pd.read_csv(_tables_file)
    st.subheader("Tables preview")
    st.dataframe(tables_df, width='stretch')
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
        st.dataframe(result_df, width='stretch')

        # Grouped summary per table with score and singles
        grouped = result_df.groupby("table")["guest"].apply(list).reset_index(name="guests_list")
        grouped["guests"] = grouped["guests_list"].apply(lambda g: ", ".join(g))
        def table_stats(g):
            percent, single_count, _ = compute_table_score_and_singles(g, guests, relationships)
            percent_val = round(100 * percent)
            # Letter grade
            if percent_val >= 90:
                grade = 'A'
            elif percent_val >= 80:
                grade = 'B'
            elif percent_val >= 70:
                grade = 'C'
            elif percent_val >= 60:
                grade = 'D'
            else:
                grade = 'F'
            return percent_val, grade, single_count
        grouped[["compatibility %", "grade", "# singles"]] = grouped["guests_list"].apply(lambda g: pd.Series(table_stats(g)))
        grouped = grouped.drop(columns=["guests_list"])
        st.subheader("Guests per table")
        st.dataframe(grouped, width='stretch')

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
