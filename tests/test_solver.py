"""
Tests for the WeddingTableMatch solver.

This module contains unit tests for the wedding table seating solver functionality.
"""

import pytest
import tempfile
import os
from src.wedding_table_match.models import Guest, Table, Relationship, RelationshipType, SeatingArrangement
from src.wedding_table_match.solver import WeddingTableSolver


class TestWeddingTableSolver:
    """Test cases for the WeddingTableSolver class."""
    
    def test_solver_initialization(self):
        """Test that the solver initializes correctly."""
        solver = WeddingTableSolver()
        assert solver.guests == []
        assert solver.tables == []
        assert solver.relationships == []
        
    def test_load_guests_from_csv(self):
        """Test loading guests from a CSV file."""
        # Create a temporary CSV file
        csv_content = """id,name,age,dietary_restrictions
1,Alice Smith,25,vegetarian
2,Bob Jones,30,
3,Carol Brown,28,gluten-free
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            temp_file = f.name
            
        try:
            solver = WeddingTableSolver()
            solver.load_guests_from_csv(temp_file)
            
            assert len(solver.guests) == 3
            
            alice = solver.guests[0]
            assert alice.id == 1
            assert alice.name == "Alice Smith"
            assert alice.age == 25
            assert alice.dietary_restrictions == "vegetarian"
            
            bob = solver.guests[1]
            assert bob.id == 2
            assert bob.name == "Bob Jones"
            assert bob.age == 30
            assert bob.dietary_restrictions is None
            
        finally:
            os.unlink(temp_file)
            
    def test_load_tables_from_csv(self):
        """Test loading tables from a CSV file."""
        csv_content = """id,name,capacity,location
1,Head Table,8,Front
2,Family Table,10,
3,Friends Table,8,Back
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            temp_file = f.name
            
        try:
            solver = WeddingTableSolver()
            solver.load_tables_from_csv(temp_file)
            
            assert len(solver.tables) == 3
            
            head_table = solver.tables[0]
            assert head_table.id == 1
            assert head_table.name == "Head Table"
            assert head_table.capacity == 8
            assert head_table.location == "Front"
            
            family_table = solver.tables[1]
            assert family_table.location is None
            
        finally:
            os.unlink(temp_file)
            
    def test_load_relationships_from_csv(self):
        """Test loading relationships from a CSV file."""
        csv_content = """guest1_id,guest2_id,relationship_type,strength
1,2,family,1.0
2,3,friend,0.8
1,4,avoid,1.0
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            temp_file = f.name
            
        try:
            solver = WeddingTableSolver()
            solver.load_relationships_from_csv(temp_file)
            
            assert len(solver.relationships) == 3
            
            rel1 = solver.relationships[0]
            assert rel1.guest1_id == 1
            assert rel1.guest2_id == 2
            assert rel1.relationship_type == RelationshipType.FAMILY
            assert rel1.strength == 1.0
            
            rel2 = solver.relationships[1]
            assert rel2.relationship_type == RelationshipType.FRIEND
            assert rel2.strength == 0.8
            
        finally:
            os.unlink(temp_file)
            
    def test_solve_placeholder(self):
        """Test the placeholder solve method."""
        solver = WeddingTableSolver()
        
        # Add some test data
        solver.guests = [
            Guest(1, "Alice"),
            Guest(2, "Bob"),
            Guest(3, "Carol")
        ]
        
        solver.tables = [
            Table(1, "Table 1", 2),
            Table(2, "Table 2", 2)
        ]
        
        arrangement = solver.solve()
        
        assert arrangement is not None
        assert len(arrangement.assignments) == 3
        assert arrangement.score > 0
        
    def test_solve_no_data(self):
        """Test solve method with no data."""
        solver = WeddingTableSolver()
        arrangement = solver.solve()
        assert arrangement is None
        
    def test_validate_solution(self):
        """Test solution validation."""
        solver = WeddingTableSolver()
        
        solver.guests = [
            Guest(1, "Alice"),
            Guest(2, "Bob")
        ]
        
        solver.tables = [
            Table(1, "Table 1", 2)
        ]
        
        # Valid arrangement
        arrangement = SeatingArrangement()
        arrangement.assign_guest_to_table(1, 1)
        arrangement.assign_guest_to_table(2, 1)
        
        assert solver.validate_solution(arrangement) is True
        
        # Invalid arrangement - over capacity
        arrangement2 = SeatingArrangement()
        arrangement2.assign_guest_to_table(1, 1)
        arrangement2.assign_guest_to_table(2, 1)
        
        solver.tables[0].capacity = 1  # Reduce capacity
        assert solver.validate_solution(arrangement2) is False
        
    def test_get_stats(self):
        """Test getting problem statistics."""
        solver = WeddingTableSolver()
        
        solver.guests = [Guest(1, "Alice"), Guest(2, "Bob")]
        solver.tables = [Table(1, "Table 1", 4), Table(2, "Table 2", 6)]
        solver.relationships = [Relationship(1, 2, RelationshipType.FRIEND)]
        
        stats = solver.get_stats()
        
        assert stats['guests'] == 2
        assert stats['tables'] == 2
        assert stats['relationships'] == 1
        assert stats['total_capacity'] == 10


class TestModels:
    """Test cases for the data models."""
    
    def test_guest_creation(self):
        """Test Guest model creation."""
        guest = Guest(1, "Alice Smith", 25, "vegetarian")
        assert guest.id == 1
        assert guest.name == "Alice Smith"
        assert guest.age == 25
        assert guest.dietary_restrictions == "vegetarian"
        assert "Alice Smith" in str(guest)
        
    def test_table_creation(self):
        """Test Table model creation."""
        table = Table(1, "Head Table", 8, "Front")
        assert table.id == 1
        assert table.name == "Head Table"
        assert table.capacity == 8
        assert table.location == "Front"
        assert "Head Table" in str(table)
        
    def test_relationship_creation(self):
        """Test Relationship model creation."""
        rel = Relationship(1, 2, RelationshipType.FAMILY, 0.9)
        assert rel.guest1_id == 1
        assert rel.guest2_id == 2
        assert rel.relationship_type == RelationshipType.FAMILY
        assert rel.strength == 0.9
        assert "family" in str(rel)
        
    def test_seating_arrangement(self):
        """Test SeatingArrangement functionality."""
        arrangement = SeatingArrangement()
        
        arrangement.assign_guest_to_table(1, 10)
        arrangement.assign_guest_to_table(2, 10)
        arrangement.assign_guest_to_table(3, 11)
        
        assert arrangement.get_table_for_guest(1) == 10
        assert arrangement.get_table_for_guest(2) == 10
        assert arrangement.get_table_for_guest(3) == 11
        assert arrangement.get_table_for_guest(999) is None
        
        guests_at_table_10 = arrangement.get_guests_at_table(10)
        assert len(guests_at_table_10) == 2
        assert 1 in guests_at_table_10
        assert 2 in guests_at_table_10
        
        guests_at_table_11 = arrangement.get_guests_at_table(11)
        assert len(guests_at_table_11) == 1
        assert 3 in guests_at_table_11