"""Tests for input validation (Phase 1.6)."""
import io
import pytest
from wedding_table_match.csv_loader import (
    load_guests, load_relationships, validate_capacity,
)
from wedding_table_match.models import Guest, Table


def _csv(text: str) -> io.StringIO:
    return io.StringIO(text.strip())


class TestDuplicateGuestIds:
    def test_rejects_duplicate_ids(self):
        csv = _csv("""
id,name
1,Alice
1,Bob
""")
        with pytest.raises(ValueError, match="Duplicate guest IDs"):
            load_guests(csv)

    def test_accepts_unique_ids(self):
        csv = _csv("""
id,name
1,Alice
2,Bob
""")
        guests = load_guests(csv)
        assert len(guests) == 2


class TestSelfReferencingRelationships:
    def test_rejects_self_reference(self):
        csv = _csv("""
guest1_id,guest2_id,relationship,strength,notes
1,1,friend,3,self
""")
        with pytest.raises(ValueError, match="Self-referencing"):
            load_relationships(csv)

    def test_accepts_normal(self):
        csv = _csv("""
guest1_id,guest2_id,relationship,strength,notes
1,2,friend,3,ok
""")
        rels = load_relationships(csv)
        assert len(rels) == 1


class TestCapacityValidation:
    def test_raises_when_over_capacity(self):
        guests = [Guest(id=str(i), name=f"G{i}") for i in range(10)]
        tables = [Table(name="T1", capacity=3)]
        with pytest.raises(ValueError, match="Not enough table capacity"):
            validate_capacity(guests, tables)

    def test_passes_when_sufficient(self):
        guests = [Guest(id=str(i), name=f"G{i}") for i in range(4)]
        tables = [Table(name="T1", capacity=3), Table(name="T2", capacity=3)]
        validate_capacity(guests, tables)  # should not raise


class TestSolverCapacityCheck:
    def test_solver_raises_on_over_capacity(self):
        from wedding_table_match.solver import SeatingModel
        guests = [Guest(id=str(i), name=f"G{i}") for i in range(5)]
        tables = [Table(name="T1", capacity=2)]
        model = SeatingModel()
        with pytest.raises(ValueError, match="Not enough capacity"):
            model.build(guests, tables, [])
