"""Streamlit UI for WeddingTableMatch with CSV previews and validations."""
from __future__ import annotations

import sys
import os
import io

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from pathlib import Path

from wedding_table_match.csv_loader import load_guests, load_tables, load_relationships
from wedding_table_match.design_data import csv_to_wedding_data, render_design_html
from wedding_table_match.models import Table
from wedding_table_match.solver import SeatingModel

DESIGN_HTML = Path(__file__).resolve().parent / "design" / "seating-planner" / "Wedding Seating Planner.html"


# -----------------------------
# Helpers
# -----------------------------

def compute_table_score_and_singles(
    guest_names: list[str],
    guests: list,
    relationships: list,
) -> tuple[float, int, list]:
    """Compute compatibility score and singles count for a set of guests at a table."""
    guest_dict = {str(g.id): g for g in guests}
    name_to_id = {g.name: str(g.id) for g in guests}
    rel_map: dict[tuple[str, str], int] = {}
    relation_scale = {
        "best friend": 5,
        "friend": 3,
        "know": 2,
        "neutral": 0,
        "avoid": -3,
        "conflict": -5,
    }
    for rel in relationships:
        a, b = str(rel.a), str(rel.b)
        score = relation_scale.get(getattr(rel, "relation", ""), getattr(rel, "strength", 0))
        rel_map[(a, b)] = score
        rel_map[(b, a)] = score

    ids = [name_to_id.get(name, name) for name in guest_names]
    n = len(ids)
    if n < 2:
        return 1.0, 0, []

    total = 0
    max_total = 0
    for i in range(n):
        for j in range(i + 1, n):
            total += rel_map.get((ids[i], ids[j]), 0)
            max_total += 5

    single_count = 0
    for name in guest_names:
        gid = name_to_id.get(name, name)
        guest = guest_dict.get(str(gid))
        if guest and getattr(guest, "single", False):
            single_count += 1

    percent = (total / max_total) if max_total > 0 else 1.0
    return percent, single_count, []


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
    maximize_known: bool,
    group_singles: bool,
    min_known: int,
    group_by_meal_preference: bool = False,
) -> tuple:
    """Run loaders, build model, and solve assignments."""
    guests_csv = df_to_csvio(guests_df)
    tables_csv = df_to_csvio(tables_df)
    rel_csv = df_to_csvio(rel_df)

    guests = load_guests(guests_csv)
    tables = load_tables(tables_csv)

    valid_ids = {str(getattr(g, "id")) for g in guests}
    relationships = load_relationships(rel_csv, valid_ids)

    model = SeatingModel(
        maximize_known=maximize_known,
        group_singles=group_singles,
        min_known=min_known,
        group_by_meal_preference=group_by_meal_preference,
    )
    model.build(guests, tables, relationships)
    return guests, relationships, model.solve()


# -----------------------------
# Editorial design system — match the floor plan iframe
# -----------------------------

st.set_page_config(
    page_title="Savett & Whitfield · Seating Plan",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,500;0,600;0,700;1,400&family=EB+Garamond:ital,wght@0,400;0,500;0,600;1,400&family=JetBrains+Mono:wght@400;500&display=swap');

    :root {
      --paper: #F5EFE6;
      --paper-2: #EFE7DA;
      --paper-3: #E8DECB;
      --ink: #2B2B2B;
      --ink-2: #4A453F;
      --ink-3: #7A7269;
      --rule: #C9BFAE;
      --walnut: #8B6F47;
      --walnut-2: #6F573A;
      --gilt: #C9A77A;
    }

    /* Force light cream palette across the whole shell, override OS dark mode */
    html, body, [data-testid="stAppViewContainer"], [data-testid="stHeader"],
    [data-testid="stMain"], [data-testid="stMainBlockContainer"], [data-testid="stSidebar"],
    .stApp, .main, section.main {
      background: var(--paper) !important;
      color: var(--ink) !important;
      font-family: 'EB Garamond', Georgia, 'Times New Roman', serif !important;
    }

    [data-testid="stSidebar"] {
      background: var(--paper-2) !important;
      border-right: 1px solid var(--rule);
    }
    [data-testid="stHeader"] { background: transparent !important; }

    h1, h2, h3, h4, h5, h6,
    [data-testid="stHeading"] {
      font-family: 'Cormorant Garamond', 'EB Garamond', Georgia, serif !important;
      color: var(--ink) !important;
      font-weight: 500 !important;
      letter-spacing: 0.01em;
    }
    h1 { font-style: italic; font-weight: 400 !important; font-size: 2.6rem !important; }
    h2 { font-size: 1.8rem !important; }

    /* Captions, labels, small text */
    p, label, .stMarkdown, [data-testid="stCaptionContainer"] {
      color: var(--ink-2) !important;
      font-family: 'EB Garamond', Georgia, serif !important;
    }
    [data-testid="stCaptionContainer"] {
      font-style: italic;
      color: var(--ink-3) !important;
    }

    /* Buttons */
    .stButton > button, .stDownloadButton > button {
      background: var(--ink) !important;
      color: var(--paper) !important;
      border: 1px solid var(--ink) !important;
      border-radius: 0 !important;
      font-family: 'EB Garamond', Georgia, serif !important;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      font-size: 0.78rem !important;
      padding: 0.55rem 1.2rem !important;
    }
    .stButton > button:hover, .stDownloadButton > button:hover {
      background: var(--walnut) !important;
      border-color: var(--walnut) !important;
    }
    .stButton > button:disabled {
      background: var(--paper-3) !important; color: var(--ink-3) !important;
      border-color: var(--rule) !important;
    }

    /* Inputs */
    input, textarea, [data-baseweb="input"] input, [data-baseweb="select"] {
      background: var(--paper) !important;
      color: var(--ink) !important;
      font-family: 'EB Garamond', serif !important;
      border-radius: 0 !important;
    }
    [data-baseweb="input"], [data-baseweb="select"] > div {
      border: 1px solid var(--rule) !important;
      border-radius: 0 !important;
      background: var(--paper) !important;
    }

    /* File uploader */
    [data-testid="stFileUploader"] section {
      background: var(--paper-2) !important;
      border: 1px dashed var(--rule) !important;
      border-radius: 0 !important;
    }
    [data-testid="stFileUploader"] button {
      background: transparent !important;
      color: var(--walnut) !important;
      border: 1px solid var(--walnut) !important;
    }

    /* Tabs */
    [data-baseweb="tab-list"] {
      gap: 0 !important;
      border-bottom: 1px solid var(--rule);
      background: transparent !important;
    }
    [data-baseweb="tab"] {
      background: transparent !important;
      color: var(--ink-3) !important;
      font-family: 'EB Garamond', serif !important;
      font-size: 0.85rem !important;
      letter-spacing: 0.18em;
      text-transform: uppercase;
      padding: 0.7rem 1.4rem !important;
      border-radius: 0 !important;
    }
    [data-baseweb="tab"][aria-selected="true"] {
      color: var(--ink) !important;
      border-bottom: 1px solid var(--ink) !important;
    }
    [data-baseweb="tab-highlight"] { background: var(--ink) !important; }

    /* Checkboxes */
    [data-testid="stCheckbox"] label p { font-family: 'EB Garamond', serif !important; }
    [data-baseweb="checkbox"] [aria-checked="true"] {
      background-color: var(--walnut) !important;
      border-color: var(--walnut) !important;
    }

    /* DataFrames */
    [data-testid="stDataFrame"] {
      background: var(--paper) !important;
      border: 1px solid var(--rule) !important;
    }

    /* Alerts */
    [data-testid="stAlert"] {
      border-radius: 0 !important;
      border-left: 2px solid var(--walnut) !important;
      background: var(--paper-2) !important;
      color: var(--ink) !important;
      font-family: 'EB Garamond', serif !important;
    }

    /* IDs and codes use mono */
    code, pre, .stCode {
      font-family: 'JetBrains Mono', ui-monospace, monospace !important;
      background: var(--paper-2) !important;
      color: var(--ink) !important;
    }

    /* Hide the default Streamlit menu noise */
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }

    /* Give the floor plan all the horizontal room it can get */
    [data-testid="stMainBlockContainer"] {
      max-width: 100% !important;
      padding-left: 1.5rem !important;
      padding-right: 1.5rem !important;
      padding-top: 1.5rem !important;
    }
    [data-testid="stIFrame"], iframe {
      width: 100% !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# -----------------------------
# Tabbed views: Floor Plan (primary) + Solver
# -----------------------------

floor_plan_tab, solver_tab = st.tabs(["Floor Plan", "Solver"])

# Solver tab is rendered first in source order so its file uploaders exist
# before the Floor Plan tab tries to read them. Visually it remains the 2nd tab.

guests_df = rel_df = tables_df = None
guests_valid = rel_valid = tables_valid = False
rel_guests_ok = True
maximize_known = False
min_known = 2
group_singles = True
group_by_meal_preference = False
_guests_file = _relationships_file = _tables_file = None

with solver_tab:
    st.markdown("#### Inputs")
    _guests_file = st.file_uploader("Guests CSV", type="csv", key="upl_guests")
    _relationships_file = st.file_uploader("Relationships CSV", type="csv", key="upl_rels")
    _tables_file = st.file_uploader("Tables CSV", type="csv", key="upl_tables")

    if _guests_file is not None:
        guests_df = pd.read_csv(_guests_file)
        if "id" in guests_df.columns:
            guests_df["id"] = guests_df["id"].astype(str)
        with st.expander("Guests preview"):
            st.dataframe(guests_df, width="stretch")
        guests_valid = validate_columns(guests_df, ["id", "name"], "guests.csv")
        _guests_file.seek(0)

    if _relationships_file is not None:
        rel_df = pd.read_csv(_relationships_file)
        for c in ("guest1_id", "guest2_id"):
            if c in rel_df.columns:
                rel_df[c] = rel_df[c].astype(str)
        with st.expander("Relationships preview"):
            st.dataframe(rel_df, width="stretch")
        rel_valid = validate_columns(rel_df, ["guest1_id", "guest2_id", "relationship"], "relationships.csv")
        _relationships_file.seek(0)

    if _tables_file is not None:
        tables_df = pd.read_csv(_tables_file)
        with st.expander("Tables preview"):
            st.dataframe(tables_df, width="stretch")
        tables_valid = validate_columns(tables_df, ["name", "capacity"], "tables.csv")
        _tables_file.seek(0)

    if guests_df is not None and rel_df is not None and guests_valid and rel_valid:
        rel_guests_ok = validate_relationship_guests(guests_df, rel_df)

    st.markdown("#### Seating options")
    col_a, col_b = st.columns(2)
    with col_a:
        maximize_known = st.checkbox(
            "Maximize known guests per table",
            value=False,
            help="Try to seat more people who know each other at the same table.",
        )
        group_singles = st.checkbox(
            "Group single guests together",
            value=True,
            help="Try to seat single guests at the same table if possible.",
        )
    with col_b:
        min_known = st.number_input(
            "Minimum known people per guest at table",
            min_value=0,
            max_value=20,
            value=2,
            help="Try to ensure each guest has at least this many known people at their table.",
        )
        group_by_meal_preference = st.checkbox(
            "Group guests by meal preference",
            value=False,
            help="Try to seat guests with the same meal preference together if possible.",
        )

    st.markdown("#### Run")

# ---- Floor Plan tab ----
with floor_plan_tab:
    st.caption(
        "Drag chairs, click tables for details, run Auto-Arrange. "
        "Upload your CSVs in the Solver tab to seat real guests; otherwise the synthetic 120-guest demo is shown."
    )
    data_override = None
    if _guests_file and _relationships_file and _tables_file and guests_valid and rel_valid and tables_valid and rel_guests_ok:
        try:
            _guests_file.seek(0); _relationships_file.seek(0); _tables_file.seek(0)
            _g = load_guests(_guests_file)
            _r = load_relationships(_relationships_file, {str(g.id) for g in _g})
            _t = load_tables(_tables_file)
            data_override = csv_to_wedding_data(_g, _t, _r)
            st.success(f"Seating {len(_g)} guests across {len(_t)} tables with {len(_r)} relationships from your CSVs.")
        except Exception as e:
            st.warning(f"Falling back to demo dataset — could not load CSVs: {e}")
        finally:
            _guests_file.seek(0); _relationships_file.seek(0); _tables_file.seek(0)
    else:
        st.info("Showing the synthetic demo dataset. Upload all three CSVs in the Solver tab to use your own data.")

    if DESIGN_HTML.exists():
        components.html(render_design_html(DESIGN_HTML, data_override=data_override), height=1800, scrolling=True)
    else:
        st.error(f"Design bundle not found at {DESIGN_HTML}.")

# ---- Solver tab ----
with solver_tab:
    run_disabled = not (_guests_file and _relationships_file and _tables_file)
    run_clicked = st.button("Run solver", disabled=run_disabled, key="run_solver_button")

    if run_clicked and not run_disabled:
        try:
            guests_df_run = uploadedfile_to_df(_guests_file)
            tables_df_run = uploadedfile_to_df(_tables_file)
            rel_df_run = uploadedfile_to_df(_relationships_file)

            if guests_df_run is None or tables_df_run is None or rel_df_run is None:
                st.error("One or more input files could not be read. Please upload valid CSV files.")
                st.stop()

            if "id" in guests_df_run.columns:
                guests_df_run["id"] = guests_df_run["id"].astype(str)
            for c in ("guest1_id", "guest2_id"):
                if c in rel_df_run.columns:
                    rel_df_run[c] = rel_df_run[c].astype(str)

            if not validate_columns(guests_df_run, ["id", "name"], "guests.csv"):
                st.stop()
            if not validate_columns(rel_df_run, ["guest1_id", "guest2_id", "relationship"], "relationships.csv"):
                st.stop()
            if not validate_columns(tables_df_run, ["name", "capacity"], "tables.csv"):
                st.stop()
            if not validate_relationship_guests(guests_df_run, rel_df_run):
                st.stop()

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
            st.dataframe(result_df, width="stretch")

            # Grouped summary per table
            grouped = result_df.groupby("table")["guest"].apply(list).reset_index(name="guests_list")
            grouped["guests"] = grouped["guests_list"].apply(lambda g: ", ".join(g))

            def table_stats(g):
                percent, single_count, _ = compute_table_score_and_singles(g, guests, relationships)
                percent_val = round(100 * percent)
                if percent_val >= 90:
                    grade = "A"
                elif percent_val >= 80:
                    grade = "B"
                elif percent_val >= 70:
                    grade = "C"
                elif percent_val >= 60:
                    grade = "D"
                else:
                    grade = "F"
                return percent_val, grade, single_count

            grouped[["compatibility %", "grade", "# singles"]] = grouped["guests_list"].apply(
                lambda g: pd.Series(table_stats(g))
            )
            grouped = grouped.drop(columns=["guests_list"])
            st.subheader("Guests per table")
            st.dataframe(grouped, width="stretch")

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
