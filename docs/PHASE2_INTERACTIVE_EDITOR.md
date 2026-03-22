# Phase 2: Interactive Seating Editor

**Goal:** Replace Streamlit with React + FastAPI. Add drag-and-drop seating editor.
**Timeline:** Weeks 4-8
**Depends on:** Phase 1 complete

---

## Architecture

```
React (TypeScript)        FastAPI (Python)         Solver Engine
├── SeatingEditor    <->  ├── /api/events      ->  SeatingModel
├── GuestManager     <->  ├── /api/guests
├── TableManager     <->  ├── /api/tables
└── FloorPlan        <->  ├── /api/relationships
                          ├── /api/solve
                          └── /api/score
```

---

## Steps

### 2.1 Scaffold FastAPI backend
- [x] Create `backend/` directory with FastAPI app
- [x] Define Pydantic models mirroring existing dataclasses (Guest, Table, Relationship)
- [x] Create API endpoints:
  - `POST /api/solve` - accept guests, tables, relationships, options; return assignments
  - `POST /api/score` - accept assignments; return per-table scores and grades
  - `POST /api/suggest-swap` - accept assignments + guest; return top swap recommendations
  - `GET /api/health` - health check
- [x] Wire endpoints to existing solver engine (import from src/)
- [x] Add CORS middleware for local dev
- [x] Write API tests with httpx/TestClient (8 tests, all passing)
- [x] Locked assignments support (partial assignment input to solver)

### 2.2 Scaffold React frontend
- [x] Create `frontend/` with Vite + React + TypeScript
- [x] Install deps: react-konva (canvas), zustand (state), tailwindcss, axios
- [ ] Set up project structure:
  ```
  frontend/src/
  ├── components/
  │   ├── FloorPlan/        # Canvas with tables and guests
  │   ├── GuestList/        # Sidebar guest list with search/filter
  │   ├── TableCard/        # Table info card with score
  │   ├── OptionsPanel/     # Solver options toggles
  │   └── ScoreBoard/       # Overall assignment quality
  ├── hooks/                # useGuests, useTables, useSolver
  ├── api/                  # API client functions
  ├── types/                # TypeScript interfaces
  └── store/                # Zustand state management
  ```

### 2.3 Guest list manager
- [ ] Table view of all guests with inline editing
- [ ] Add/delete guest rows
- [ ] CSV import (drag-drop or file picker)
- [ ] CSV export
- [ ] Column sorting and filtering
- [ ] Search by name

### 2.4 Table manager
- [ ] Add/remove/rename tables
- [ ] Set capacity per table
- [ ] Set table shape (round, rectangular, long)
- [ ] Visual preview of table layout

### 2.5 Relationship editor
- [ ] Click two guests to set/edit relationship
- [ ] Relationship type dropdown (best friend -> conflict)
- [ ] Bulk CSV import for relationships
- [ ] Visual indicator on floor plan (colored edges between guests)

### 2.6 Floor plan with drag-and-drop
- [ ] Canvas rendering of tables (positioned by shape)
- [ ] Guest nodes on tables, color-coded by compatibility
- [ ] Drag guest from one table to another
- [ ] Real-time score update on drop (call /api/score)
- [ ] Hover tooltip: guest info, relationship summary
- [ ] Zoom and pan controls

### 2.7 Solver integration
- [ ] "Auto-assign" button calls /api/solve
- [ ] Results populate the floor plan
- [ ] "Lock" guests in place (partial assignment input to solver)
- [ ] "Suggest swap" on right-click: shows best swap options with score delta

### 2.8 Undo/redo
- [ ] Track assignment history in Zustand store
- [ ] Ctrl+Z / Ctrl+Y keyboard shortcuts
- [ ] Undo stack depth: 50 actions

### 2.9 Options panel
- [ ] Mirror all solver toggles from current Streamlit sidebar
- [ ] Group by category: relationships, demographics, constraints
- [ ] Changes trigger re-solve suggestion (not auto-solve)

---

## Acceptance Criteria
- User can upload CSVs, run solver, see results on visual floor plan
- User can drag guests between tables with real-time score updates
- User can lock guests and re-run solver on remaining
- Undo/redo works for all manual changes
- API response time < 2s for 200 guests
- All API endpoints have tests
