# Phase 1: Stabilize the Prototype

**Goal:** Make the existing Streamlit app reliable, testable, and ready for migration.
**Timeline:** Weeks 1-3
**Status:** Complete (2 minor items deferred)

---

## Steps

### 1.1 Fix hardcoded file paths in app.py
- [x] Replace hardcoded local paths with Streamlit file uploaders
- [x] Remove dead test code

### 1.2 Clean up utils.py
- [x] Remove duplicate SeatingModel class (~200 lines of stale code)
- [x] Keep only: sample CSV generators, SEATING_OPTIONS dict, get_seating_options()

### 1.3 Fix requirements.txt
- [x] Add missing deps: networkx, pyvis
- [x] Pin version ranges for reproducibility

### 1.4 Add missing tables_sample.csv
- [x] Create tables_sample.csv with sample data matching guests_sample.csv

### 1.5 Write unit tests
- [x] test_models.py: parse_pipe_list, parse_bool, Guest/Table/Relationship defaults
- [x] test_csv_loader.py: load_guests, load_tables, load_relationships, validation
- [x] test_solver.py: relation_value, compute_table_stats, grade_tables, SeatingModel (5-guest, 20-guest, edge cases, constraint enforcement)

### 1.6 Input validation improvements
- [x] Detect duplicate guest IDs in CSV and raise clear error
- [x] Detect self-referencing relationships (guest related to self)
- [x] Warn when total guest count exceeds total table capacity (validate_capacity)
- [x] Validate relationship types against known scale (warning on unrecognized)
- [x] Handle solver over-capacity gracefully (raises ValueError in build())

### 1.7 Fix ID/name fragility in solver
- [x] Normalized all lookups to use string IDs consistently
- [ ] Remove dual id/name indexing that causes redundant Relationship objects (deferred: works but wasteful)
- [x] Add integration test: CSV -> load -> solve -> verify all guests assigned

### 1.8 Code quality
- [x] Add type hints to app.py helper functions
- [x] Remove unused imports (io imported twice in app.py)
- [x] Create conftest.py with shared test fixtures
- [ ] Add docstrings to all public functions in solver.py (deferred: not blocking)

---

## Acceptance Criteria
- All 40+ tests pass
- No hardcoded paths
- `pip install -r requirements.txt && pytest` works from clean venv
- Solver raises ValueError when capacity is insufficient
- No duplicate code between utils.py and solver.py
