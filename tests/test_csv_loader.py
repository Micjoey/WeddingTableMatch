"""Tests for CSV loading."""
import io
import pytest
from wedding_table_match.csv_loader import load_guests, load_tables, load_relationships


def _csv_buf(text: str) -> io.StringIO:
    """Create a StringIO buffer from CSV text."""
    return io.StringIO(text.strip())


# --- load_guests ---

class TestLoadGuests:
    BASIC_CSV = """
id,name,age,gender_identity,rsvp,meal_preference,single,interested_in,plus_one,sit_with_partner,min_known,min_unknown,weight,must_with,must_separate,groups,hobbies,languages,relationship_status,forced_table,location,diet_choices,partner
1,Alice,29,Female,Yes,Vegetarian,True,reading|hiking,False,True,1,0,1,Bob,,Friends,reading|yoga,English|Spanish,single,,New York,vegetarian,2
2,Bob,31,Male,Yes,Chicken,False,,False,True,1,0,1,Alice,,Friends,,English,single,,New York,,1
"""

    def test_loads_two_guests(self):
        guests = load_guests(_csv_buf(self.BASIC_CSV))
        assert len(guests) == 2

    def test_guest_fields(self):
        guests = load_guests(_csv_buf(self.BASIC_CSV))
        alice = guests[0]
        assert alice.name == "Alice"
        assert alice.age == 29
        assert alice.single is True
        assert alice.hobbies == ["reading", "yoga"]
        assert alice.languages == ["English", "Spanish"]
        assert alice.must_with == ["Bob"]

    def test_invalid_must_with_reference(self):
        csv = """
id,name,age,gender_identity,rsvp,meal_preference,single,interested_in,plus_one,sit_with_partner,min_known,min_unknown,weight,must_with,must_separate,groups,hobbies,languages,relationship_status,forced_table,location,diet_choices,partner
1,Alice,29,Female,Yes,Veg,False,,False,True,0,0,1,NonExistent,,,,,,,,
"""
        with pytest.raises(ValueError, match="Unknown guest"):
            load_guests(_csv_buf(csv))

    def test_minimal_csv(self):
        csv = """
id,name
1,Alice
2,Bob
"""
        guests = load_guests(_csv_buf(csv))
        assert len(guests) == 2
        assert guests[0].age == 0
        assert guests[0].single is False


# --- load_tables ---

class TestLoadTables:
    def test_basic(self):
        csv = """
name,capacity,tags
Table 1,8,VIP
Table 2,10,
"""
        tables = load_tables(_csv_buf(csv))
        assert len(tables) == 2
        assert tables[0].capacity == 8
        assert tables[0].tags == ["VIP"]
        assert tables[1].tags == []


# --- load_relationships ---

class TestLoadRelationships:
    def test_basic(self):
        csv = """
guest1_id,guest2_id,relationship,strength,notes
1,2,friend,3,pals
"""
        rels = load_relationships(_csv_buf(csv))
        assert len(rels) == 1
        assert rels[0].relation == "friend"
        assert rels[0].strength == 3

    def test_validation_rejects_unknown_ids(self):
        csv = """
guest1_id,guest2_id,relationship,strength,notes
1,99,friend,3,
"""
        with pytest.raises(ValueError, match="unknown guest"):
            load_relationships(_csv_buf(csv), guest_names={"1", "2"})

    def test_validation_passes_known_ids(self):
        csv = """
guest1_id,guest2_id,relationship,strength,notes
1,2,friend,3,
"""
        rels = load_relationships(_csv_buf(csv), guest_names={"1", "2"})
        assert len(rels) == 1
