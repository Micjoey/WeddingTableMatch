# WeddingTableMatch: Product Requirements Document

**Version:** 1.0
**Date:** 2026-03-20
**Author:** Macallan Savett

---

## 1. Problem Statement

Seating arrangements are one of the most stressful parts of wedding planning. Couples and planners must balance dozens of constraints: who knows whom, who to keep apart, dietary needs, accessibility, group dynamics, and table capacity. Most people solve this with spreadsheets, sticky notes, or trial and error. The result is hours of manual work and suboptimal outcomes.

WeddingTableMatch solves this with an algorithm that suggests seating assignments based on guest relationships and preferences, then lets users manually adjust.

---

## 2. Users

**Primary: Engaged couples** planning their own wedding. Typically managing 50-200 guests. Non-technical. Need a simple interface that "just works."

**Secondary: Professional wedding planners** managing multiple events simultaneously. Managing 100-500+ guests per event. Need efficiency, multi-event support, and export capabilities.

---

## 3. Current State (Prototype)

### What exists

| Component | Status | Notes |
|-----------|--------|-------|
| Guest data model | Working | 23 fields: demographics, preferences, constraints, relationships, dietary needs |
| Relationship model | Working | Scored scale: best friend (+5) to conflict (-5) |
| Table model | Working | Name, capacity, tags |
| Solver (beam search) | Working | Beam search + greedy fallback + local pair-swap hill climbing + rebalancing |
| Hard constraints | Working | must_with, must_separate, avoid relationships, forced table |
| Soft preferences | Working | 12 toggleable criteria (hobbies, languages, age, location, diet, etc.) |
| CSV import | Working | Guests, relationships, tables loaded from CSV |
| CLI | Working | Full-featured with all solver toggles |
| Streamlit UI | Partial | Basic upload/solve/download flow; hardcoded file paths for testing |
| Mind map visualization | Working | Pyvis network graph with color-coded tables, relationship edges, tooltips |
| Grading system | Working | A-F grades per table based on mean relationship scores |

### Tech stack

- Python 3.12, Streamlit, Pandas, NetworkX, Pyvis
- No database, no auth, no persistent storage
- No tests (referenced in README but not present)

### Known issues

1. `app.py` lines 186-188: hardcoded local file paths instead of file uploaders
2. `utils.py`: contains a duplicate, older version of `SeatingModel` mixed with utility functions
3. `requirements.txt` is incomplete (missing networkx, pyvis)
4. No `tables_sample.csv` in repo root (referenced in app.py)
5. No test suite
6. Solver is name-based internally but CSV uses IDs, causing fragile lookups
7. No way to manually adjust assignments after solver runs (core feature gap)

---

## 4. Target Experience

### Core flow

1. **Import guests**: Upload CSV or enter manually in a table editor
2. **Define tables**: Set table names, capacities, and optional tags
3. **Define relationships**: Upload CSV or use a visual relationship builder
4. **Configure preferences**: Toggle solver options (group singles, match hobbies, etc.)
5. **Run solver**: Algorithm generates suggested seating
6. **Review and adjust**: Visual floor plan with drag-and-drop to move guests between tables. Per-table compatibility scores update in real time.
7. **Export**: Download assignments as CSV, PDF seating chart, or printable place cards

### The "auto-suggest + manual" model

The solver produces a starting point. The user then adjusts using a visual editor. Every manual change triggers a re-score so the user sees the impact. The solver should also offer "what if" suggestions: "If you move Alice to Table 3, compatibility drops from B to C."

---

## 5. Feature Roadmap

### Phase 1: Stabilize the prototype (weeks 1-3)

**Goal:** Make the existing Streamlit app reliable and usable.

- Fix hardcoded file paths; restore file uploaders
- Clean up `utils.py` (remove duplicate SeatingModel, keep only utility functions)
- Complete `requirements.txt` (add networkx, pyvis, and pin versions)
- Add `tables_sample.csv` to repo
- Write unit tests for: models, csv_loader, solver (at minimum: 5-guest and 20-guest scenarios, edge cases like empty relationships, single table, over-capacity)
- Add input validation: duplicate guest IDs, self-referencing relationships, capacity < guest count warnings
- Fix ID/name fragility in solver lookups

### Phase 2: Interactive seating editor (weeks 4-8)

**Goal:** Users can visually adjust solver output.

- Replace Streamlit with a React frontend (Streamlit is too limiting for drag-and-drop interaction)
- Build a visual floor plan: tables as circles/rectangles, guests as draggable nodes
- Real-time compatibility scoring on every move
- Undo/redo stack
- "Swap suggestion" feature: click a guest, see recommended swaps ranked by score improvement
- Keep Python backend as an API (FastAPI or Flask)
- Guest list editor: add/edit/delete guests inline without CSV re-upload
- Relationship editor: click two guests to set their relationship

### Phase 3: Polish and planner features (weeks 9-14)

**Goal:** Production-quality for couples; useful for planners.

- User accounts and saved events
- Multiple events per account (planner support)
- PDF export: printable seating chart with table numbers and guest names
- Place card generator (PDF)
- Guest RSVP tracking integration (import from common wedding sites)
- Shareable read-only link for seating chart review
- Mobile-responsive web UI
- Accessibility: keyboard navigation for the seating editor, screen reader labels

### Phase 4: Mobile and advanced (post-launch)

- React Native mobile app or PWA
- AI-powered suggestions: "Based on the guest data, here are 3 seating arrangements optimized for different priorities"
- Collaborative editing (multiple planners working simultaneously)
- Venue floor plan templates (round tables, long tables, U-shape, etc.)
- Integration with wedding planning platforms (Zola, The Knot, etc.)

---

## 6. Data Model

### Guest (existing, solid)

```
id, name, age, gender_identity, rsvp, meal_preference, single,
interested_in, plus_one, sit_with_partner, min_known, min_unknown,
weight, must_with, must_separate, groups, hobbies, languages,
relationship_status, forced_table, location, diet_choices, partner
```

**Proposed additions:**
- `accessibility_needs` (string): wheelchair, hearing, vision, mobility
- `vip` (bool): head table priority
- `notes` (string): free-text for planner notes

### Relationship (existing, solid)

```
guest1_id, guest2_id, relationship, strength, notes
```

Relationship types: best friend (+5), friend (+3), know (+2), neutral (0), avoid (-3), conflict (-5)

### Table (existing, extend)

```
name, capacity, tags
```

**Proposed additions:**
- `shape` (enum): round, rectangular, long
- `position_x`, `position_y` (float): floor plan coordinates
- `min_guests` (int): minimum fill threshold

---

## 7. Architecture Direction

### Current: Monolith (Streamlit)

```
CSV files -> csv_loader -> models -> solver -> Streamlit UI
```

### Target: Decoupled frontend + API

```
React frontend  <-->  REST API (FastAPI)  <-->  Solver engine
                           |
                       PostgreSQL (events, guests, assignments)
```

**Key decisions:**

- **Frontend:** React + TypeScript. The seating editor needs fine-grained DOM control that Streamlit cannot provide. Use a canvas library (Konva.js or React Flow) for the drag-and-drop floor plan.
- **Backend:** FastAPI. The solver is Python; keep it in Python. FastAPI gives async support and auto-generated OpenAPI docs.
- **Database:** PostgreSQL. Relational data (guests, tables, relationships) fits naturally. SQLAlchemy or Prisma as ORM.
- **Solver stays as-is:** The beam search + hill climbing approach is sound for the problem size (up to ~500 guests). No need for a constraint solver library (OR-Tools, etc.) unless performance becomes an issue at scale.

**Trade-off:** Migrating from Streamlit to React is a significant rewrite. The alternative is to push Streamlit further with custom components, but that creates a ceiling for the interactive editor. React is the right call for the target experience.

---

## 8. Solver Algorithm Notes

The current solver uses:
1. Union-Find to group must_with guests
2. Optional regrouping by meal preference or singles
3. Beam search (width 8-10) over group-to-table assignments
4. Greedy fallback if beam search fails
5. Local pair-swap hill climbing (up to 14 iterations)
6. Target-size rebalancing pass

**Strengths:** Handles hard constraints well. Flexible scoring with 12+ toggleable criteria. Fast for typical wedding sizes (50-200 guests).

**Weaknesses:** O(n^2) pair comparisons in hill climbing. No randomized restarts. Beam width is fixed. No way to seed with a partial manual assignment.

**Recommended improvements:**
- Accept partial assignments as input (user locks some guests, solver fills the rest)
- Add randomized restarts (run solver 3-5 times with shuffled group order, take best)
- Make beam width adaptive based on problem size
- Cache relationship lookups (currently rebuilds for every feasibility check)

---

## 9. Success Metrics

| Metric | Target |
|--------|--------|
| Solver runtime (200 guests, 20 tables) | < 5 seconds |
| User can go from CSV upload to first result | < 2 minutes |
| Manual adjustment (drag guest to new table) | < 200ms UI response |
| Zero hard constraint violations in output | 100% |
| Test coverage (solver + loader + models) | > 80% |

---

## 10. Risks and Open Questions

**Risks:**
- Streamlit-to-React migration is the largest effort. If scope creeps, Phase 2 could stall. Mitigate by keeping the API layer thin and the solver untouched.
- Guest data is sensitive (names, relationships, dietary info). Any persistent storage needs encryption at rest and proper auth from day one.
- The solver's greedy/heuristic nature means it cannot guarantee optimal solutions. Users may get frustrated if manual adjustments consistently outperform the algorithm. Mitigate with randomized restarts and clear messaging ("this is a suggestion, not the answer").

**Open questions:**
1. Should the MVP support collaborative editing, or is single-user sufficient for launch?
2. What wedding platforms (Zola, The Knot, etc.) are highest priority for import integration?
3. Is there a target guest count ceiling? The current algorithm may need rethinking above 500 guests.
4. Should the relationship builder support importing from social media (Facebook friend lists, etc.)?
