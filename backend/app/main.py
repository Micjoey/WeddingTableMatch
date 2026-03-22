"""FastAPI application for WeddingTableMatch."""
from __future__ import annotations

import sys
import os

# Add solver source to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .schemas import (
    SolveRequest, SolveResponse, ScoreRequest, SwapRequest,
    SwapResponse, SwapSuggestion, TableScore,
)
from .solver_bridge import (
    convert_to_domain, run_solver, score_assignments, suggest_swaps,
)

app = FastAPI(
    title="WeddingTableMatch API",
    description="Seating optimization engine for weddings",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health():
    """Health check endpoint."""
    return {"status": "ok"}


@app.post("/api/solve", response_model=SolveResponse)
def solve(request: SolveRequest):
    """Run the seating solver and return assignments with scores."""
    try:
        guests, tables, relationships = convert_to_domain(
            request.guests, request.tables, request.relationships,
        )
        assignments = run_solver(
            guests, tables, relationships,
            options=request.options,
            locked=request.locked_assignments,
        )
        table_scores = score_assignments(guests, relationships, assignments)
        return SolveResponse(assignments=assignments, table_scores=table_scores)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@app.post("/api/score", response_model=list[TableScore])
def score(request: ScoreRequest):
    """Score an existing assignment without re-solving."""
    try:
        guests, _, relationships = convert_to_domain(
            request.guests, [], request.relationships,
        )
        return score_assignments(guests, relationships, request.assignments)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@app.post("/api/suggest-swap", response_model=SwapResponse)
def swap(request: SwapRequest):
    """Suggest the best swaps for a given guest."""
    try:
        guests, tables, relationships = convert_to_domain(
            request.guests, request.tables, request.relationships,
        )
        suggestions = suggest_swaps(
            guests, tables, relationships,
            request.assignments, request.guest_name,
        )
        return SwapResponse(suggestions=suggestions)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
