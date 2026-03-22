"""Pydantic models for the WeddingTableMatch API."""
from __future__ import annotations

from pydantic import BaseModel, Field


class GuestIn(BaseModel):
    """Guest input for the solver API."""
    id: str
    name: str
    age: int = 0
    gender_identity: str = ""
    rsvp: str = ""
    meal_preference: str = ""
    single: bool = False
    interested_in: list[str] = Field(default_factory=list)
    plus_one: bool = False
    sit_with_partner: bool = True
    min_known: int = 0
    min_unknown: int = 0
    weight: int = 1
    must_with: list[str] = Field(default_factory=list)
    must_separate: list[str] = Field(default_factory=list)
    groups: list[str] = Field(default_factory=list)
    hobbies: list[str] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)
    relationship_status: str = ""
    forced_table: str = ""
    location: str = ""
    diet_choices: list[str] = Field(default_factory=list)
    partner: str = ""


class TableIn(BaseModel):
    """Table input for the solver API."""
    name: str
    capacity: int
    tags: list[str] = Field(default_factory=list)


class RelationshipIn(BaseModel):
    """Relationship input for the solver API."""
    guest1_id: str
    guest2_id: str
    relationship: str = "neutral"
    strength: int = 0
    notes: str = ""


class SolverOptions(BaseModel):
    """Solver configuration options."""
    maximize_known: bool = False
    group_singles: bool = False
    min_known: int = 0
    group_by_meal_preference: bool = False
    equalize_tables: bool = False
    balance_weight: float = 12.0
    min_target_slack: int = 0
    match_hobbies: bool = False
    match_languages: bool = False
    match_age: bool = False
    match_relationship_status: bool = False
    match_location: bool = False
    match_diet: bool = False
    respect_forced_table: bool = False


class SolveRequest(BaseModel):
    """Full solve request."""
    guests: list[GuestIn]
    tables: list[TableIn]
    relationships: list[RelationshipIn]
    options: SolverOptions = Field(default_factory=SolverOptions)
    locked_assignments: dict[str, str] = Field(
        default_factory=dict,
        description="Guest name -> table name for locked assignments. Solver fills the rest.",
    )


class ScoreRequest(BaseModel):
    """Request to score an existing assignment."""
    guests: list[GuestIn]
    relationships: list[RelationshipIn]
    assignments: dict[str, str]  # guest name -> table name


class SwapRequest(BaseModel):
    """Request swap suggestions for a specific guest."""
    guests: list[GuestIn]
    tables: list[TableIn]
    relationships: list[RelationshipIn]
    assignments: dict[str, str]
    guest_name: str


class TableScore(BaseModel):
    """Per-table scoring result."""
    table: str
    members: list[str]
    total_score: int
    mean_score: float
    grade: str
    pos_pairs: int
    neg_pairs: int
    neu_pairs: int


class SolveResponse(BaseModel):
    """Solver output."""
    assignments: dict[str, str]
    table_scores: list[TableScore]


class SwapSuggestion(BaseModel):
    """A suggested swap with score delta."""
    guest_name: str
    from_table: str
    to_table: str
    score_delta: float


class SwapResponse(BaseModel):
    """Swap suggestion output."""
    suggestions: list[SwapSuggestion]
