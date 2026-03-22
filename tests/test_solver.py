"""Tests for the seating solver."""
import pytest
from wedding_table_match.models import Guest, Table, Relationship
from wedding_table_match.solver import SeatingModel, relation_value, compute_table_stats, grade_tables


# --- relation_value ---

class TestRelationValue:
    def test_known_types(self):
        assert relation_value(Relationship(a="1", b="2", relation="best friend")) == 5
        assert relation_value(Relationship(a="1", b="2", relation="friend")) == 3
        assert relation_value(Relationship(a="1", b="2", relation="know")) == 2
        assert relation_value(Relationship(a="1", b="2", relation="neutral")) == 0
        assert relation_value(Relationship(a="1", b="2", relation="avoid")) == -3
        assert relation_value(Relationship(a="1", b="2", relation="conflict")) == -5

    def test_unknown_type_uses_strength(self):
        r = Relationship(a="1", b="2", relation="custom", strength=4)
        assert relation_value(r) == 4


# --- compute_table_stats ---

class TestComputeTableStats:
    def _get_rel(self, rels_dict):
        def getter(a, b):
            return rels_dict.get((a, b), Relationship(a=a, b=b, relation="neutral"))
        return getter

    def test_two_friends(self):
        rels = {("A", "B"): Relationship(a="A", b="B", relation="friend")}
        stats = compute_table_stats(["A", "B"], self._get_rel(rels))
        assert stats["total_score"] == 3
        assert stats["pos_pairs"] == 1
        assert stats["neg_pairs"] == 0

    def test_empty_table(self):
        stats = compute_table_stats([], self._get_rel({}))
        assert stats["total_score"] == 0
        assert stats["pair_count"] == 0

    def test_single_guest(self):
        stats = compute_table_stats(["A"], self._get_rel({}))
        assert stats["pair_count"] == 0


# --- grade_tables ---

class TestGradeTables:
    def test_grades(self):
        stats = [
            {"mean_score": 3.0, "total_score": 9, "pair_count": 3, "pos_pairs": 3, "neg_pairs": 0, "neu_pairs": 0},
            {"mean_score": 0.0, "total_score": 0, "pair_count": 3, "pos_pairs": 0, "neg_pairs": 0, "neu_pairs": 3},
        ]
        graded = grade_tables(stats)
        assert graded[0]["grade"] == "A"
        assert graded[1]["grade"] == "F"


# --- SeatingModel ---

def _make_guests(n):
    """Create n simple guests."""
    return [Guest(id=str(i), name=f"Guest{i}") for i in range(1, n + 1)]


def _make_tables(names_caps):
    """Create tables from list of (name, capacity) tuples."""
    return [Table(name=n, capacity=c) for n, c in names_caps]


class TestSeatingModelBasic:
    def test_five_guests_two_tables(self):
        """Basic scenario: 5 guests, 2 tables of 3."""
        guests = _make_guests(5)
        tables = _make_tables([("T1", 3), ("T2", 3)])
        rels = [
            Relationship(a="Guest1", b="Guest2", relation="friend", strength=3),
            Relationship(a="Guest3", b="Guest4", relation="friend", strength=3),
        ]
        model = SeatingModel()
        model.build(guests, tables, rels)
        assignments = model.solve()

        # All guests assigned
        assert len(assignments) == 5
        # No table over capacity
        for t in ["T1", "T2"]:
            count = sum(1 for v in assignments.values() if v == t)
            assert count <= 3

    def test_must_separate_honored(self):
        """Guests with must_separate should not be at the same table."""
        guests = [
            Guest(id="1", name="Alice", must_separate=["Bob"]),
            Guest(id="2", name="Bob", must_separate=["Alice"]),
            Guest(id="3", name="Carol"),
            Guest(id="4", name="David"),
        ]
        tables = _make_tables([("T1", 2), ("T2", 2)])
        model = SeatingModel()
        model.build(guests, tables, [])
        assignments = model.solve()

        assert assignments["Alice"] != assignments["Bob"]

    def test_must_with_honored(self):
        """Guests with must_with should be at the same table."""
        guests = [
            Guest(id="1", name="Alice", must_with=["Bob"]),
            Guest(id="2", name="Bob", must_with=["Alice"]),
            Guest(id="3", name="Carol"),
            Guest(id="4", name="David"),
        ]
        tables = _make_tables([("T1", 3), ("T2", 3)])
        model = SeatingModel()
        model.build(guests, tables, [])
        assignments = model.solve()

        assert assignments["Alice"] == assignments["Bob"]

    def test_avoid_relationship_separated(self):
        """Guests with 'avoid' relationship should not be at the same table."""
        guests = _make_guests(4)
        tables = _make_tables([("T1", 2), ("T2", 2)])
        rels = [Relationship(a="Guest1", b="Guest2", relation="avoid", strength=-3)]
        model = SeatingModel()
        model.build(guests, tables, rels)
        assignments = model.solve()

        assert assignments["Guest1"] != assignments["Guest2"]

    def test_single_table(self):
        """All guests fit in one table."""
        guests = _make_guests(3)
        tables = _make_tables([("T1", 5)])
        model = SeatingModel()
        model.build(guests, tables, [])
        assignments = model.solve()

        assert all(v == "T1" for v in assignments.values())

    def test_over_capacity_raises(self):
        """More guests than total capacity should raise during build."""
        guests = _make_guests(5)
        tables = _make_tables([("T1", 2)])
        model = SeatingModel()
        with pytest.raises(ValueError, match="Not enough capacity"):
            model.build(guests, tables, [])


class TestSeatingModelLarger:
    def test_twenty_guests_four_tables(self):
        """20 guests across 4 tables of 6."""
        guests = _make_guests(20)
        tables = _make_tables([
            ("T1", 6), ("T2", 6), ("T3", 6), ("T4", 6),
        ])
        # Create some friend clusters
        rels = []
        for i in range(1, 5):
            rels.append(Relationship(a=f"Guest{i}", b=f"Guest{i+1}", relation="friend", strength=3))
        for i in range(10, 14):
            rels.append(Relationship(a=f"Guest{i}", b=f"Guest{i+1}", relation="friend", strength=3))

        model = SeatingModel()
        model.build(guests, tables, rels)
        assignments = model.solve()

        assert len(assignments) == 20
        for t in ["T1", "T2", "T3", "T4"]:
            count = sum(1 for v in assignments.values() if v == t)
            assert count <= 6

    def test_group_singles(self):
        """Singles grouping should cluster single guests."""
        guests = [
            Guest(id="1", name="A", single=True),
            Guest(id="2", name="B", single=True),
            Guest(id="3", name="C", single=True),
            Guest(id="4", name="D", single=False),
            Guest(id="5", name="E", single=False),
            Guest(id="6", name="F", single=False),
        ]
        tables = _make_tables([("T1", 4), ("T2", 4)])
        model = SeatingModel(group_singles=True)
        model.build(guests, tables, [])
        assignments = model.solve()

        # All singles should be at the same table
        singles_tables = {assignments["A"], assignments["B"], assignments["C"]}
        assert len(singles_tables) == 1


class TestSeatingModelEdgeCases:
    def test_empty_relationships(self):
        """Solver works with no relationships at all."""
        guests = _make_guests(4)
        tables = _make_tables([("T1", 2), ("T2", 2)])
        model = SeatingModel()
        model.build(guests, tables, [])
        assignments = model.solve()
        assert len(assignments) == 4

    def test_one_guest_one_table(self):
        """Trivial case."""
        guests = _make_guests(1)
        tables = _make_tables([("T1", 1)])
        model = SeatingModel()
        model.build(guests, tables, [])
        assignments = model.solve()
        assert assignments["Guest1"] == "T1"
