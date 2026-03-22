"""Shared test fixtures for WeddingTableMatch."""
import io
import pytest
from wedding_table_match.models import Guest, Table, Relationship


@pytest.fixture
def five_guests():
    """Five guests with varied attributes."""
    return [
        Guest(id="1", name="Alice", age=29, single=True, hobbies=["reading", "yoga"]),
        Guest(id="2", name="Bob", age=31, single=False, hobbies=["reading", "sports"]),
        Guest(id="3", name="Carol", age=27, single=True, meal_preference="Fish"),
        Guest(id="4", name="David", age=35, single=False, meal_preference="Beef"),
        Guest(id="5", name="Eve", age=28, single=True, meal_preference="Vegetarian"),
    ]


@pytest.fixture
def two_tables():
    """Two tables with capacity 3 each."""
    return [Table(name="T1", capacity=3), Table(name="T2", capacity=3)]


@pytest.fixture
def four_tables():
    """Four tables with capacity 6 each."""
    return [
        Table(name="T1", capacity=6),
        Table(name="T2", capacity=6),
        Table(name="T3", capacity=6),
        Table(name="T4", capacity=6),
    ]


@pytest.fixture
def basic_relationships():
    """A few sample relationships."""
    return [
        Relationship(a="1", b="2", relation="friend", strength=3),
        Relationship(a="3", b="4", relation="friend", strength=3),
    ]


def csv_buf(text: str) -> io.StringIO:
    """Create a StringIO buffer from CSV text (strips leading whitespace per line)."""
    return io.StringIO(text.strip())
