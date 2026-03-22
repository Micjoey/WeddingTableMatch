"""Bridge between FastAPI schemas and the solver engine."""
from __future__ import annotations

from itertools import combinations
from typing import Dict, List, Tuple

from wedding_table_match.models import Guest, Table, Relationship
from wedding_table_match.solver import SeatingModel, compute_table_stats, grade_tables, relation_value

from .schemas import (
    GuestIn, TableIn, RelationshipIn, SolverOptions, TableScore, SwapSuggestion,
)


def convert_to_domain(
    guests_in: list[GuestIn],
    tables_in: list[TableIn],
    rels_in: list[RelationshipIn],
) -> Tuple[List[Guest], List[Table], List[Relationship]]:
    """Convert Pydantic models to solver domain objects."""
    guests = [
        Guest(
            id=g.id, name=g.name, age=g.age,
            gender_identity=g.gender_identity, rsvp=g.rsvp,
            meal_preference=g.meal_preference, single=g.single,
            interested_in=g.interested_in, plus_one=g.plus_one,
            sit_with_partner=g.sit_with_partner,
            min_known=g.min_known, min_unknown=g.min_unknown,
            weight=g.weight, must_with=g.must_with,
            must_separate=g.must_separate, groups=g.groups,
            hobbies=g.hobbies, languages=g.languages,
            relationship_status=g.relationship_status,
            forced_table=g.forced_table, location=g.location,
            diet_choices=g.diet_choices, partner=g.partner,
        )
        for g in guests_in
    ]
    tables = [
        Table(name=t.name, capacity=t.capacity, tags=t.tags)
        for t in tables_in
    ]
    relationships = [
        Relationship(
            a=r.guest1_id, b=r.guest2_id,
            relation=r.relationship, strength=r.strength, notes=r.notes,
        )
        for r in rels_in
    ]
    return guests, tables, relationships


def run_solver(
    guests: List[Guest],
    tables: List[Table],
    relationships: List[Relationship],
    options: SolverOptions | None = None,
    locked: Dict[str, str] | None = None,
) -> Dict[str, str]:
    """Run the solver with given options. Supports locked (pre-assigned) guests."""
    opts = options or SolverOptions()

    if locked:
        # Remove locked guests from the solve pool
        locked_names = set(locked.keys())
        free_guests = [g for g in guests if g.name not in locked_names]

        # Reduce table capacities by locked assignments
        locked_counts: Dict[str, int] = {}
        for table in locked.values():
            locked_counts[table] = locked_counts.get(table, 0) + 1

        adjusted_tables = [
            Table(
                name=t.name,
                capacity=max(0, t.capacity - locked_counts.get(t.name, 0)),
                tags=t.tags,
            )
            for t in tables
        ]
    else:
        free_guests = guests
        adjusted_tables = tables

    model = SeatingModel(
        maximize_known=opts.maximize_known,
        group_singles=opts.group_singles,
        min_known=opts.min_known,
        group_by_meal_preference=opts.group_by_meal_preference,
        equalize_tables=opts.equalize_tables,
        balance_weight=opts.balance_weight,
        min_target_slack=opts.min_target_slack,
        match_hobbies=opts.match_hobbies,
        match_languages=opts.match_languages,
        match_age=opts.match_age,
        match_relationship_status=opts.match_relationship_status,
        match_location=opts.match_location,
        match_diet=opts.match_diet,
        respect_forced_table=opts.respect_forced_table,
    )
    model.build(free_guests, adjusted_tables, relationships)
    assignments = model.solve()

    # Merge locked assignments back in
    if locked:
        assignments.update(locked)

    return assignments


def score_assignments(
    guests: List[Guest],
    relationships: List[Relationship],
    assignments: Dict[str, str],
) -> List[TableScore]:
    """Score the current assignments, returning per-table stats."""
    # Build a temporary model just for relationship lookups
    model = SeatingModel()
    # Use a dummy table list just to avoid the capacity check
    dummy_tables = [Table(name="dummy", capacity=len(guests))]
    model.build(guests, dummy_tables, relationships)

    # Group by table
    table_to_members: Dict[str, List[str]] = {}
    for guest, table in assignments.items():
        table_to_members.setdefault(table, []).append(guest)

    stats = []
    for table_name in sorted(table_to_members.keys()):
        members = sorted(table_to_members[table_name])
        s = compute_table_stats(members, model.get_relationship)
        s["table"] = table_name
        s["members"] = members
        stats.append(s)

    graded = grade_tables(stats)

    return [
        TableScore(
            table=s["table"],
            members=s["members"],
            total_score=s["total_score"],
            mean_score=round(s["mean_score"], 4),
            grade=s["grade"],
            pos_pairs=s["pos_pairs"],
            neg_pairs=s["neg_pairs"],
            neu_pairs=s["neu_pairs"],
        )
        for s in graded
    ]


def suggest_swaps(
    guests: List[Guest],
    tables: List[Table],
    relationships: List[Relationship],
    assignments: Dict[str, str],
    guest_name: str,
    max_suggestions: int = 5,
) -> List[SwapSuggestion]:
    """Find the best table swaps for a guest, ranked by score improvement."""
    if guest_name not in assignments:
        raise ValueError(f"Guest '{guest_name}' not found in assignments")

    current_table = assignments[guest_name]
    all_tables = {t.name for t in tables}
    other_tables = all_tables - {current_table}

    # Build model for scoring
    model = SeatingModel()
    dummy_tables = [Table(name="dummy", capacity=len(guests))]
    model.build(guests, dummy_tables, relationships)

    # Current total score
    table_members: Dict[str, List[str]] = {}
    for g, t in assignments.items():
        table_members.setdefault(t, []).append(g)

    def total_score(members_map: Dict[str, List[str]]) -> float:
        total = 0.0
        for members in members_map.values():
            if len(members) >= 2:
                total += compute_table_stats(members, model.get_relationship)["total_score"]
        return total

    base_score = total_score(table_members)
    suggestions = []

    for target_table in other_tables:
        # Simulate moving guest_name to target_table
        new_members = {}
        for t, members in table_members.items():
            new_members[t] = [m for m in members if m != guest_name]
        new_members.setdefault(target_table, [])
        new_members[target_table].append(guest_name)

        # Check capacity
        table_cap = {t.name: t.capacity for t in tables}
        if len(new_members.get(target_table, [])) > table_cap.get(target_table, 0):
            continue

        new_score = total_score(new_members)
        delta = new_score - base_score

        suggestions.append(SwapSuggestion(
            guest_name=guest_name,
            from_table=current_table,
            to_table=target_table,
            score_delta=round(delta, 2),
        ))

    suggestions.sort(key=lambda s: s.score_delta, reverse=True)
    return suggestions[:max_suggestions]
