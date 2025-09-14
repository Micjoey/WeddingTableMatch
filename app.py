
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

# Preview uploaded data
if _guests_file is not None:
    guests_df = pd.read_csv(_guests_file)
    st.subheader("Guests preview")
    st.dataframe(guests_df)
if _relationships_file is not None:
    rel_df = pd.read_csv(_relationships_file)
    st.subheader("Relationships preview")
    st.dataframe(rel_df)
if _tables_file is not None:
    tables_df = pd.read_csv(_tables_file)
    st.subheader("Tables preview")
    st.dataframe(tables_df)

# Solve when all files available and button pressed
if _guests_file and _relationships_file and _tables_file:
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
