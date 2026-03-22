// ---- Domain types matching backend Pydantic schemas exactly ----

export interface Guest {
  id: string;
  name: string;
  age: number;
  gender_identity: string;
  rsvp: string;
  meal_preference: string;
  single: boolean;
  interested_in: string[];
  plus_one: boolean;
  sit_with_partner: boolean;
  min_known: number;
  min_unknown: number;
  weight: number;
  must_with: string[];
  must_separate: string[];
  groups: string[];
  hobbies: string[];
  languages: string[];
  relationship_status: string;
  forced_table: string;
  location: string;
  diet_choices: string[];
  partner: string;
}

export type TableShape = 'round' | 'rect' | 'long';

export interface Table {
  name: string;
  capacity: number;
  tags: string[];
  shape?: TableShape;
  rotation?: number; // degrees, frontend-only
  // Frontend-only: floor plan position
  x?: number;
  y?: number;
}

export interface Relationship {
  guest1_id: string;
  guest2_id: string;
  relationship: string;
  strength: number;
  notes: string;
}

export interface SolverOptions {
  maximize_known: boolean;
  group_singles: boolean;
  min_known: number;
  group_by_meal_preference: boolean;
  equalize_tables: boolean;
  balance_weight: number;
  min_target_slack: number;
  match_hobbies: boolean;
  match_languages: boolean;
  match_age: boolean;
  match_relationship_status: boolean;
  match_location: boolean;
  match_diet: boolean;
  respect_forced_table: boolean;
}

// ---- API request/response types ----

export interface SolveRequest {
  guests: Guest[];
  tables: Table[];
  relationships: Relationship[];
  options: SolverOptions;
  locked_assignments: Record<string, string>; // guest name -> table name
}

export interface ScoreRequest {
  guests: Guest[];
  relationships: Relationship[];
  assignments: Record<string, string>; // guest name -> table name
}

export interface SwapRequest {
  guests: Guest[];
  tables: Table[];
  relationships: Relationship[];
  assignments: Record<string, string>;
  guest_name: string;
}

export interface TableScore {
  table: string;
  members: string[];
  total_score: number;
  mean_score: number;
  grade: string;
  pos_pairs: number;
  neg_pairs: number;
  neu_pairs: number;
}

export interface SolveResponse {
  assignments: Record<string, string>;
  table_scores: TableScore[];
}

export interface ScoreResponse {
  table_scores: TableScore[];
}

export interface SwapSuggestion {
  guest_name: string;
  from_table: string;
  to_table: string;
  score_delta: number;
}

export interface SwapResponse {
  suggestions: SwapSuggestion[];
}

// ---- Helper: create a default guest ----

export function createDefaultGuest(name: string): Guest {
  return {
    id: `guest-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`,
    name,
    age: 0,
    gender_identity: '',
    rsvp: '',
    meal_preference: '',
    single: false,
    interested_in: [],
    plus_one: false,
    sit_with_partner: true,
    min_known: 0,
    min_unknown: 0,
    weight: 1,
    must_with: [],
    must_separate: [],
    groups: [],
    hobbies: [],
    languages: [],
    relationship_status: '',
    forced_table: '',
    location: '',
    diet_choices: [],
    partner: '',
  };
}

export function createDefaultOptions(): SolverOptions {
  return {
    maximize_known: false,
    group_singles: false,
    min_known: 0,
    group_by_meal_preference: false,
    equalize_tables: false,
    balance_weight: 12.0,
    min_target_slack: 0,
    match_hobbies: false,
    match_languages: false,
    match_age: false,
    match_relationship_status: false,
    match_location: false,
    match_diet: false,
    respect_forced_table: false,
  };
}
