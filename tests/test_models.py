"""Tests for data models."""
import math
import pytest
from wedding_table_match.models import (
    Guest, Table, Relationship,
    parse_pipe_list, parse_bool, parse_interested_in,
)


# --- parse_pipe_list ---

class TestParsePipeList:
    def test_normal(self):
        assert parse_pipe_list("a|b|c") == ["a", "b", "c"]

    def test_whitespace(self):
        assert parse_pipe_list(" a | b ") == ["a", "b"]

    def test_none(self):
        assert parse_pipe_list(None) == []

    def test_empty_string(self):
        assert parse_pipe_list("") == []

    def test_nan_float(self):
        assert parse_pipe_list(float("nan")) == []

    def test_nan_string(self):
        assert parse_pipe_list("nan") == []

    def test_single_value(self):
        assert parse_pipe_list("solo") == ["solo"]

    def test_empty_segments_filtered(self):
        assert parse_pipe_list("a||b") == ["a", "b"]


# --- parse_bool ---

class TestParseBool:
    def test_true(self):
        assert parse_bool("True") is True
        assert parse_bool("true") is True
        assert parse_bool(" True ") is True

    def test_false(self):
        assert parse_bool("False") is False
        assert parse_bool("") is False
        assert parse_bool("no") is False

    def test_non_string(self):
        assert parse_bool(True) is True
        assert parse_bool(False) is False


# --- Guest defaults ---

class TestGuestDefaults:
    def test_minimal_guest(self):
        g = Guest(id="1", name="Test")
        assert g.age == 0
        assert g.single is False
        assert g.must_with == []
        assert g.must_separate == []
        assert g.hobbies == []
        assert g.partner == ""

    def test_full_guest(self):
        g = Guest(
            id="1", name="Alice", age=29, single=True,
            must_with=["Bob"], hobbies=["reading", "yoga"],
            languages=["English", "Spanish"],
        )
        assert g.single is True
        assert len(g.must_with) == 1
        assert len(g.hobbies) == 2


# --- Table ---

class TestTable:
    def test_defaults(self):
        t = Table(name="T1", capacity=10)
        assert t.tags == []

    def test_with_tags(self):
        t = Table(name="T1", capacity=8, tags=["VIP", "front"])
        assert len(t.tags) == 2


# --- Relationship ---

class TestRelationship:
    def test_defaults(self):
        r = Relationship(a="1", b="2", relation="friend")
        assert r.strength == 0
        assert r.notes == ""
