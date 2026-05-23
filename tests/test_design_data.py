"""Tests for the design-data adapter that converts our Python models into
the JS-shaped object the Floor Plan Designer prototype expects.

The prototype reads ``window.WEDDING_DATA`` with this shape:
    {
      guests: [{id, name, first, last, age, gender_identity, rsvp,
                meal_preference, single, plus_one, sit_with_partner,
                groups: [key], groupLabel, hobbies, languages,
                relationship_status, location, diet_choices, partner,
                vip, accessibility, notes}],
      tables: [{name, capacity, tags, shape}],
      relationships: [{guest1_id, guest2_id, relationship, strength, notes}],
      initialAssignments: {guest_id: table_name},
      groups: [{key, label}],
      diets: [{key, label}],
    }

These tests pin that contract.
"""
from __future__ import annotations

import json

import pytest

from pathlib import Path

from wedding_table_match.design_data import (
    csv_to_wedding_data,
    render_design_html,
    wedding_data_to_js,
)
from wedding_table_match.models import Guest, Relationship, Table

DESIGN_HTML = (
    Path(__file__).resolve().parent.parent
    / "design"
    / "seating-planner"
    / "Wedding Seating Planner.html"
)


# ---------- guest mapping ----------

class TestGuestMapping:
    def test_basic_fields_passthrough(self):
        guests = [Guest(id="1", name="Alice Chen", age=29, gender_identity="Female",
                        rsvp="Yes", meal_preference="Vegetarian", single=False,
                        relationship_status="married", location="Brooklyn",
                        groups=["Friends"], hobbies=["reading"], languages=["English"],
                        diet_choices=["vegetarian"], partner="2")]
        out = csv_to_wedding_data(guests, [], [])
        g = out["guests"][0]
        assert g["id"] == "1"
        assert g["name"] == "Alice Chen"
        assert g["age"] == 29
        assert g["gender_identity"] == "Female"
        assert g["rsvp"] == "Yes"
        assert g["meal_preference"] == "Vegetarian"
        assert g["single"] is False
        assert g["relationship_status"] == "married"
        assert g["location"] == "Brooklyn"
        assert g["partner"] == "2"

    def test_first_last_split(self):
        guests = [Guest(id="1", name="Alice Chen"), Guest(id="2", name="Madonna")]
        out = csv_to_wedding_data(guests, [], [])
        assert out["guests"][0]["first"] == "Alice"
        assert out["guests"][0]["last"] == "Chen"
        # Single-token name: first set, last empty
        assert out["guests"][1]["first"] == "Madonna"
        assert out["guests"][1]["last"] == ""

    def test_first_last_handles_multi_word_last_name(self):
        guests = [Guest(id="1", name="Iris van der Berg")]
        out = csv_to_wedding_data(guests, [], [])
        assert out["guests"][0]["first"] == "Iris"
        assert out["guests"][0]["last"] == "van der Berg"

    def test_lists_passthrough(self):
        guests = [Guest(id="1", name="A B", groups=["Friends", "Bridal"],
                        hobbies=["reading", "yoga"], languages=["English", "Spanish"],
                        diet_choices=["vegan", "gluten-free"])]
        out = csv_to_wedding_data(guests, [], [])
        g = out["guests"][0]
        assert g["groups"] == ["Friends", "Bridal"]
        assert g["hobbies"] == ["reading", "yoga"]
        assert g["languages"] == ["English", "Spanish"]
        assert g["diet_choices"] == ["vegan", "gluten-free"]

    def test_group_label_is_first_group(self):
        guests = [Guest(id="1", name="A B", groups=["Bride's Family", "VIP"])]
        out = csv_to_wedding_data(guests, [], [])
        assert out["guests"][0]["groupLabel"] == "Bride's Family"

    def test_group_label_empty_when_no_groups(self):
        guests = [Guest(id="1", name="A B", groups=[])]
        out = csv_to_wedding_data(guests, [], [])
        assert out["guests"][0]["groupLabel"] == ""

    def test_vip_flag_from_groups(self):
        # vip is not a Guest field — derived from groups containing "VIP" or "Bridal Party"
        guests = [
            Guest(id="1", name="A B", groups=["Bridal Party"]),
            Guest(id="2", name="C D", groups=["VIP"]),
            Guest(id="3", name="E F", groups=["Friends"]),
        ]
        out = csv_to_wedding_data(guests, [], [])
        assert out["guests"][0]["vip"] is True
        assert out["guests"][1]["vip"] is True
        assert out["guests"][2]["vip"] is False

    def test_accessibility_defaults_none(self):
        guests = [Guest(id="1", name="A B")]
        out = csv_to_wedding_data(guests, [], [])
        assert out["guests"][0]["accessibility"] is None

    def test_initial_assignments_from_forced_table(self):
        guests = [
            Guest(id="1", name="A B", forced_table="Magnolia"),
            Guest(id="2", name="C D"),  # no forced_table
            Guest(id="3", name="E F", forced_table="Wisteria"),
        ]
        out = csv_to_wedding_data(guests, [], [])
        assert out["initialAssignments"] == {"1": "Magnolia", "3": "Wisteria"}


# ---------- table mapping ----------

class TestTableMapping:
    def test_basic(self):
        tables = [Table(name="Table 1", capacity=8, tags=["Family"])]
        out = csv_to_wedding_data([], tables, [])
        t = out["tables"][0]
        assert t["name"] == "Table 1"
        assert t["capacity"] == 8
        assert t["tags"] == ["Family"]

    def test_default_shape_round(self):
        tables = [Table(name="T1", capacity=8)]
        out = csv_to_wedding_data([], tables, [])
        assert out["tables"][0]["shape"] == "round"


# ---------- relationship mapping ----------

class TestRelationshipMapping:
    def test_passthrough(self):
        rels = [Relationship(a="1", b="2", relation="friend", strength=3, notes="college")]
        out = csv_to_wedding_data([], [], rels)
        r = out["relationships"][0]
        assert r["guest1_id"] == "1"
        assert r["guest2_id"] == "2"
        assert r["relationship"] == "friend"
        assert r["strength"] == 3
        assert r["notes"] == "college"


# ---------- groups & diets indexes ----------

class TestGroupsIndex:
    def test_groups_collected_from_guests(self):
        guests = [
            Guest(id="1", name="A B", groups=["Friends"]),
            Guest(id="2", name="C D", groups=["Friends", "Bridal Party"]),
            Guest(id="3", name="E F", groups=["Family"]),
        ]
        out = csv_to_wedding_data(guests, [], [])
        keys = sorted(g["key"] for g in out["groups"])
        assert keys == ["Bridal Party", "Family", "Friends"]
        # Each entry has key & label (key == label for CSV-derived data)
        for g in out["groups"]:
            assert g["key"] == g["label"]

    def test_diets_collected_from_guests(self):
        guests = [
            Guest(id="1", name="A B", diet_choices=["vegan"]),
            Guest(id="2", name="C D", diet_choices=["vegetarian", "gluten-free"]),
        ]
        out = csv_to_wedding_data(guests, [], [])
        keys = sorted(d["key"] for d in out["diets"])
        assert "vegan" in keys
        assert "vegetarian" in keys
        assert "gluten-free" in keys


# ---------- JSON-serializability + JS embed ----------

class TestSerialization:
    def test_full_dict_is_json_serializable(self):
        guests = [Guest(id="1", name="Alice Chen", age=29, groups=["Friends"],
                        hobbies=["reading"], diet_choices=["vegan"])]
        tables = [Table(name="T1", capacity=8, tags=["Family"])]
        rels = [Relationship(a="1", b="1", relation="friend", strength=3)]
        out = csv_to_wedding_data(guests, tables, rels)
        json.dumps(out)  # must not raise

    def test_wedding_data_to_js_assigns_global(self):
        out = csv_to_wedding_data([Guest(id="1", name="A B")], [], [])
        js = wedding_data_to_js(out)
        assert "window.WEDDING_DATA" in js
        # JSON body should round-trip
        prefix = "window.WEDDING_DATA = "
        body = js[js.index(prefix) + len(prefix):].rstrip(";").strip()
        parsed = json.loads(body)
        assert parsed["guests"][0]["id"] == "1"


# ---------- empty/edge cases ----------

class TestEdgeCases:
    def test_empty_inputs(self):
        out = csv_to_wedding_data([], [], [])
        assert out == {
            "guests": [], "tables": [], "relationships": [],
            "initialAssignments": {}, "groups": [], "diets": [],
        }

    def test_render_design_html_inlines_assets(self):
        if not DESIGN_HTML.exists():
            pytest.skip("design bundle missing")
        out = render_design_html(DESIGN_HTML)
        assert "<style>" in out
        assert "WEDDING_DATA" in out  # data.js inlined
        assert 'src="prototype/' not in out  # no dangling local refs
        assert "unpkg.com/react@" in out  # remote CDN scripts preserved

    def test_end_to_end_csv_to_rendered_html(self):
        """Full pipeline: load real sample CSVs -> convert -> render."""
        if not DESIGN_HTML.exists():
            pytest.skip("design bundle missing")
        from wedding_table_match.csv_loader import (
            load_guests, load_relationships, load_tables,
        )
        root = Path(__file__).resolve().parent.parent
        g_path = root / "guests_full_sample.csv"
        r_path = root / "relationships_full_sample.csv"
        t_path = root / "tables_full_sample.csv"
        if not (g_path.exists() and r_path.exists() and t_path.exists()):
            pytest.skip("full sample CSVs not present")
        guests = load_guests(g_path)
        rels = load_relationships(r_path, {str(g.id) for g in guests})
        tables = load_tables(t_path)
        data = csv_to_wedding_data(guests, tables, rels)
        out = render_design_html(DESIGN_HTML, data_override=data)
        assert len(out) > 50_000  # full app inlined
        assert "WEDDING_DATA" in out
        # Some real names from the sample appear
        assert "Alice Chen" in out or "Bob Chen" in out
        # Real table names from the sample appear
        assert "Table 1" in out

    def test_render_design_html_data_override_replaces_dataset(self):
        if not DESIGN_HTML.exists():
            pytest.skip("design bundle missing")
        guests = [Guest(id="42", name="Test User", groups=["Friends"])]
        tables = [Table(name="OnlyTable", capacity=4)]
        data = csv_to_wedding_data(guests, tables, [])
        out = render_design_html(DESIGN_HTML, data_override=data)
        # The synthetic dataset's marker fingerprints should not be present
        assert "Realistic wedding dataset" not in out
        assert "mulberry32" not in out  # synthetic RNG only lives in data.js
        # Our overridden data should be embedded
        assert '"OnlyTable"' in out
        assert '"Test User"' in out
        # Single global assignment
        assert out.count("window.WEDDING_DATA") == 1

    def test_guest_without_optional_fields(self):
        out = csv_to_wedding_data([Guest(id="1", name="Solo")], [], [])
        g = out["guests"][0]
        # Required keys all present
        for key in ["id", "name", "first", "last", "age", "gender_identity",
                    "rsvp", "meal_preference", "single", "plus_one",
                    "sit_with_partner", "groups", "groupLabel", "hobbies",
                    "languages", "relationship_status", "location",
                    "diet_choices", "partner", "vip", "accessibility", "notes"]:
            assert key in g, f"missing key {key}"
