"""Integration tests: CSV -> load -> solve -> verify."""
import io
import pytest
from wedding_table_match.csv_loader import load_guests, load_tables, load_relationships
from wedding_table_match.solver import SeatingModel


GUESTS_CSV = """
id,name,age,gender_identity,rsvp,meal_preference,single,interested_in,plus_one,sit_with_partner,min_known,min_unknown,weight,must_with,must_separate,groups,hobbies,languages,relationship_status,forced_table,location,diet_choices,partner
1,Alice,29,Female,Yes,Vegetarian,True,reading|hiking,False,True,1,0,1,Bob,,Friends,reading|yoga,English|Spanish,single,,New York,vegetarian|gluten-free,2
2,Bob,31,Male,Yes,Chicken,False,reading|sports,False,True,1,0,1,Alice,,Friends,reading|yoga,English,single,,New York,none,1
3,Carol,27,Female,Yes,Fish,True,travel|music,False,True,1,0,1,,,Family,music|travel,French|English,single,,Paris,vegan,
4,David,35,Male,Yes,Beef,False,golf|cooking,False,True,1,0,1,,,Work,golf|cooking,English|German,married,,Berlin,none,5
5,Eve,28,Female,Yes,Vegetarian,True,reading|music,False,True,1,0,1,,,Friends,reading|music,English,single,,New York,vegetarian,4
""".strip()

RELATIONSHIPS_CSV = """
guest1_id,guest2_id,relationship,strength,notes
1,2,friend,3,Alice and Bob are friends
1,3,know,2,Alice knows Carol
2,3,neutral,0,Bob and Carol are neutral
4,5,friend,3,David and Eve are friends
""".strip()

TABLES_CSV = """
name,capacity,tags
Table 1,3,Friends
Table 2,3,Family
""".strip()


class TestEndToEnd:
    def test_csv_to_assignments(self):
        """Full pipeline: CSV text -> load -> solve -> all guests assigned."""
        guests = load_guests(io.StringIO(GUESTS_CSV))
        tables = load_tables(io.StringIO(TABLES_CSV))
        guest_ids = {str(g.id) for g in guests}
        relationships = load_relationships(io.StringIO(RELATIONSHIPS_CSV), guest_ids)

        model = SeatingModel()
        model.build(guests, tables, relationships)
        assignments = model.solve()

        # Every guest is assigned
        assert len(assignments) == len(guests)

        # Every assignment is to a valid table
        table_names = {t.name for t in tables}
        for table in assignments.values():
            assert table in table_names

        # No table over capacity
        table_caps = {t.name: t.capacity for t in tables}
        for tname in table_names:
            count = sum(1 for v in assignments.values() if v == tname)
            assert count <= table_caps[tname], f"{tname} over capacity: {count} > {table_caps[tname]}"

    def test_must_with_enforced_end_to_end(self):
        """Alice must_with Bob: they should end up at the same table."""
        guests = load_guests(io.StringIO(GUESTS_CSV))
        tables = load_tables(io.StringIO(TABLES_CSV))
        guest_ids = {str(g.id) for g in guests}
        relationships = load_relationships(io.StringIO(RELATIONSHIPS_CSV), guest_ids)

        model = SeatingModel()
        model.build(guests, tables, relationships)
        assignments = model.solve()

        assert assignments["Alice"] == assignments["Bob"]

    def test_larger_scenario(self):
        """20 guests, 4 tables: all assigned, no over-capacity."""
        # Build 20 guests programmatically
        rows = ["id,name"]
        for i in range(1, 21):
            rows.append(f"{i},Guest{i}")
        guests_csv = "\n".join(rows)

        tables_csv = "name,capacity\nT1,6\nT2,6\nT3,6\nT4,6"
        rels_csv = "guest1_id,guest2_id,relationship,strength,notes\n1,2,friend,3,pals\n3,4,friend,3,pals"

        guests = load_guests(io.StringIO(guests_csv))
        tables = load_tables(io.StringIO(tables_csv))
        guest_ids = {str(g.id) for g in guests}
        relationships = load_relationships(io.StringIO(rels_csv), guest_ids)

        model = SeatingModel()
        model.build(guests, tables, relationships)
        assignments = model.solve()

        assert len(assignments) == 20
        for tname in ["T1", "T2", "T3", "T4"]:
            count = sum(1 for v in assignments.values() if v == tname)
            assert count <= 6
