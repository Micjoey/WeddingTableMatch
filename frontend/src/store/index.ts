import { create } from 'zustand';
import {
  Guest,
  Table,
  Relationship,
  SolverOptions,
  TableScore,
  createDefaultOptions,
} from '../types';
import { apiClient } from '../api/client';

// Assignments: guest name -> table name (matches backend contract)
type Assignments = Record<string, string>;

interface AppState {
  // Data
  guests: Guest[];
  tables: Table[];
  relationships: Relationship[];
  assignments: Assignments;
  lockedGuests: Set<string>; // guest names that are locked
  options: SolverOptions;

  // Scores (from backend)
  tableScores: TableScore[];

  // UI state
  selectedTableName: string | null;
  selectedGuestName: string | null;
  isLoading: boolean;
  error: string | null;

  // Undo/redo: snapshots of assignments
  undoStack: Assignments[];
  redoStack: Assignments[];

  // Data mutations
  setGuests: (guests: Guest[]) => void;
  addGuest: (guest: Guest) => void;
  removeGuest: (guestName: string) => void;
  updateGuest: (oldName: string, guest: Guest) => void;

  setTables: (tables: Table[]) => void;
  addTable: (table: Table) => void;
  removeTable: (tableName: string) => void;
  updateTable: (oldName: string, table: Table) => void;

  setRelationships: (relationships: Relationship[]) => void;
  addRelationship: (rel: Relationship) => void;
  removeRelationship: (guest1Id: string, guest2Id: string) => void;

  // Assignment mutations (push to undo stack)
  setAssignment: (guestName: string, tableName: string) => void;
  removeAssignment: (guestName: string) => void;
  setAllAssignments: (assignments: Assignments) => void;
  clearAssignments: () => void;

  toggleLockGuest: (guestName: string) => void;
  setOptions: (options: SolverOptions) => void;

  // Selection
  selectTable: (tableName: string | null) => void;
  selectGuest: (guestName: string | null) => void;

  // Solver API calls
  solve: () => Promise<void>;
  updateScores: () => Promise<void>;

  // History
  undo: () => void;
  redo: () => void;

  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
}

// Save current assignments to undo stack, clear redo
function pushUndo(state: AppState): Partial<AppState> {
  return {
    undoStack: [...state.undoStack.slice(-19), { ...state.assignments }],
    redoStack: [],
  };
}

export const useAppStore = create<AppState>((set, get) => ({
  guests: [],
  tables: [],
  relationships: [],
  assignments: {},
  lockedGuests: new Set(),
  options: createDefaultOptions(),
  tableScores: [],
  selectedTableName: null,
  selectedGuestName: null,
  isLoading: false,
  error: null,
  undoStack: [],
  redoStack: [],

  // ---- Guest mutations ----
  setGuests: (guests) => set({ guests }),

  addGuest: (guest) =>
    set((state) => ({ guests: [...state.guests, guest] })),

  removeGuest: (guestName) =>
    set((state) => {
      const newAssignments = { ...state.assignments };
      delete newAssignments[guestName];
      return {
        guests: state.guests.filter((g) => g.name !== guestName),
        assignments: newAssignments,
        lockedGuests: new Set(
          Array.from(state.lockedGuests).filter((n) => n !== guestName)
        ),
      };
    }),

  updateGuest: (oldName, guest) =>
    set((state) => {
      const newGuests = state.guests.map((g) =>
        g.name === oldName ? guest : g
      );
      // If name changed, update assignments key
      const newAssignments = { ...state.assignments };
      if (oldName !== guest.name && newAssignments[oldName] !== undefined) {
        newAssignments[guest.name] = newAssignments[oldName];
        delete newAssignments[oldName];
      }
      return { guests: newGuests, assignments: newAssignments };
    }),

  // ---- Table mutations ----
  setTables: (tables) => set({ tables }),

  addTable: (table) =>
    set((state) => ({ tables: [...state.tables, table] })),

  removeTable: (tableName) =>
    set((state) => ({
      tables: state.tables.filter((t) => t.name !== tableName),
      assignments: Object.fromEntries(
        Object.entries(state.assignments).filter(([, t]) => t !== tableName)
      ),
    })),

  updateTable: (oldName, table) =>
    set((state) => {
      const newTables = state.tables.map((t) =>
        t.name === oldName ? table : t
      );
      // If name changed, update assignment values
      const newAssignments: Assignments = {};
      for (const [guest, tbl] of Object.entries(state.assignments)) {
        newAssignments[guest] = tbl === oldName ? table.name : tbl;
      }
      return { tables: newTables, assignments: newAssignments };
    }),

  // ---- Relationship mutations ----
  setRelationships: (relationships) => set({ relationships }),

  addRelationship: (rel) =>
    set((state) => ({ relationships: [...state.relationships, rel] })),

  removeRelationship: (guest1Id, guest2Id) =>
    set((state) => ({
      relationships: state.relationships.filter(
        (r) =>
          !(
            (r.guest1_id === guest1Id && r.guest2_id === guest2Id) ||
            (r.guest1_id === guest2Id && r.guest2_id === guest1Id)
          )
      ),
    })),

  // ---- Assignment mutations ----
  setAssignment: (guestName, tableName) =>
    set((state) => ({
      ...pushUndo(state),
      assignments: { ...state.assignments, [guestName]: tableName },
    })),

  removeAssignment: (guestName) =>
    set((state) => {
      const newAssignments = { ...state.assignments };
      delete newAssignments[guestName];
      return { ...pushUndo(state), assignments: newAssignments };
    }),

  setAllAssignments: (assignments) =>
    set((state) => ({
      ...pushUndo(state),
      assignments,
    })),

  clearAssignments: () =>
    set((state) => ({
      ...pushUndo(state),
      assignments: {},
    })),

  toggleLockGuest: (guestName) =>
    set((state) => {
      const newLocked = new Set(state.lockedGuests);
      if (newLocked.has(guestName)) {
        newLocked.delete(guestName);
      } else {
        newLocked.add(guestName);
      }
      return { lockedGuests: newLocked };
    }),

  setOptions: (options) => set({ options }),

  // ---- Selection ----
  selectTable: (tableName) => set({ selectedTableName: tableName }),
  selectGuest: (guestName) => set({ selectedGuestName: guestName }),

  // ---- Solver ----
  solve: async () => {
    const state = get();
    if (state.guests.length === 0 || state.tables.length === 0) {
      set({ error: 'Need at least one guest and one table to solve.' });
      return;
    }

    set({ isLoading: true, error: null });

    try {
      // Build locked assignments from lockedGuests
      const locked: Record<string, string> = {};
      for (const guestName of state.lockedGuests) {
        if (state.assignments[guestName]) {
          locked[guestName] = state.assignments[guestName];
        }
      }

      const response = await apiClient.solve({
        guests: state.guests,
        tables: state.tables,
        relationships: state.relationships,
        options: state.options,
        locked_assignments: locked,
      });

      // Push current to undo, set new assignments
      set((s) => ({
        ...pushUndo(s),
        assignments: response.assignments,
        tableScores: response.table_scores,
        isLoading: false,
      }));
    } catch (error) {
      const message =
        error instanceof Error ? error.message : 'Unknown error';
      set({ error: `Solver failed: ${message}`, isLoading: false });
    }
  },

  updateScores: async () => {
    const state = get();
    if (Object.keys(state.assignments).length === 0) {
      set({ tableScores: [] });
      return;
    }

    set({ isLoading: true, error: null });

    try {
      const scores = await apiClient.score({
        guests: state.guests,
        relationships: state.relationships,
        assignments: state.assignments,
      });

      set({ tableScores: scores, isLoading: false });
    } catch (error) {
      const message =
        error instanceof Error ? error.message : 'Unknown error';
      set({ error: `Scoring failed: ${message}`, isLoading: false });
    }
  },

  // ---- Undo/Redo ----
  undo: () =>
    set((state) => {
      if (state.undoStack.length === 0) return state;
      const previous = state.undoStack[state.undoStack.length - 1];
      return {
        assignments: previous,
        undoStack: state.undoStack.slice(0, -1),
        redoStack: [...state.redoStack, { ...state.assignments }],
      };
    }),

  redo: () =>
    set((state) => {
      if (state.redoStack.length === 0) return state;
      const next = state.redoStack[state.redoStack.length - 1];
      return {
        assignments: next,
        redoStack: state.redoStack.slice(0, -1),
        undoStack: [...state.undoStack, { ...state.assignments }],
      };
    }),

  setLoading: (loading) => set({ isLoading: loading }),
  setError: (error) => set({ error }),
}));
