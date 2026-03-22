"""API endpoint tests."""
import pytest
from fastapi.testclient import TestClient

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from app.main import app

client = TestClient(app)


FIVE_GUESTS = [
    {"id": "1", "name": "Alice", "single": True, "must_with": ["Bob"]},
    {"id": "2", "name": "Bob", "must_with": ["Alice"]},
    {"id": "3", "name": "Carol"},
    {"id": "4", "name": "David"},
    {"id": "5", "name": "Eve"},
]

TWO_TABLES = [
    {"name": "T1", "capacity": 3},
    {"name": "T2", "capacity": 3},
]

RELATIONSHIPS = [
    {"guest1_id": "1", "guest2_id": "2", "relationship": "friend", "strength": 3},
    {"guest1_id": "3", "guest2_id": "4", "relationship": "friend", "strength": 3},
]


class TestHealth:
    def test_health(self):
        r = client.get("/api/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"


class TestSolve:
    def test_basic_solve(self):
        r = client.post("/api/solve", json={
            "guests": FIVE_GUESTS,
            "tables": TWO_TABLES,
            "relationships": RELATIONSHIPS,
        })
        assert r.status_code == 200
        data = r.json()
        assert len(data["assignments"]) == 5
        assert len(data["table_scores"]) > 0

    def test_must_with_honored(self):
        r = client.post("/api/solve", json={
            "guests": FIVE_GUESTS,
            "tables": TWO_TABLES,
            "relationships": RELATIONSHIPS,
        })
        data = r.json()
        assert data["assignments"]["Alice"] == data["assignments"]["Bob"]

    def test_locked_assignments(self):
        r = client.post("/api/solve", json={
            "guests": FIVE_GUESTS,
            "tables": TWO_TABLES,
            "relationships": RELATIONSHIPS,
            "locked_assignments": {"Carol": "T2"},
        })
        data = r.json()
        assert data["assignments"]["Carol"] == "T2"

    def test_over_capacity_returns_422(self):
        r = client.post("/api/solve", json={
            "guests": FIVE_GUESTS,
            "tables": [{"name": "T1", "capacity": 2}],
            "relationships": [],
        })
        assert r.status_code == 422


class TestScore:
    def test_score_assignments(self):
        # First solve
        solve_r = client.post("/api/solve", json={
            "guests": FIVE_GUESTS,
            "tables": TWO_TABLES,
            "relationships": RELATIONSHIPS,
        })
        assignments = solve_r.json()["assignments"]

        # Then score
        r = client.post("/api/score", json={
            "guests": FIVE_GUESTS,
            "relationships": RELATIONSHIPS,
            "assignments": assignments,
        })
        assert r.status_code == 200
        scores = r.json()
        assert len(scores) > 0
        assert "grade" in scores[0]


class TestSwap:
    def test_suggest_swaps(self):
        # First solve
        solve_r = client.post("/api/solve", json={
            "guests": FIVE_GUESTS,
            "tables": TWO_TABLES,
            "relationships": RELATIONSHIPS,
        })
        assignments = solve_r.json()["assignments"]

        r = client.post("/api/suggest-swap", json={
            "guests": FIVE_GUESTS,
            "tables": TWO_TABLES,
            "relationships": RELATIONSHIPS,
            "assignments": assignments,
            "guest_name": "Carol",
        })
        assert r.status_code == 200
        data = r.json()
        assert "suggestions" in data

    def test_unknown_guest_returns_422(self):
        r = client.post("/api/suggest-swap", json={
            "guests": FIVE_GUESTS,
            "tables": TWO_TABLES,
            "relationships": [],
            "assignments": {"Alice": "T1"},
            "guest_name": "Nobody",
        })
        assert r.status_code == 422
