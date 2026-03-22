import React, { useRef, useState } from 'react';
import { useAppStore } from '../../store';
import { Guest, Table, Relationship, createDefaultGuest } from '../../types';
import { RandomizerModal } from '../RandomizerModal/RandomizerModal';

// Parse a CSV string into rows of objects keyed by header
function parseCSV(text: string): Record<string, string>[] {
  const lines = text.trim().split('\n');
  if (lines.length < 2) return [];
  const headers = lines[0].split(',').map((h) => h.trim());
  return lines.slice(1).map((line) => {
    const values = line.split(',').map((v) => v.trim());
    const row: Record<string, string> = {};
    headers.forEach((h, i) => {
      row[h] = values[i] || '';
    });
    return row;
  });
}

// Convert a pipe-separated string to an array
function parsePipe(val: string): string[] {
  if (!val) return [];
  return val.split('|').map((s) => s.trim()).filter(Boolean);
}

// ---- Sample data ----

const SAMPLE_GUESTS: Guest[] = [
  { ...createDefaultGuest('Alice'), id: '1', age: 29, gender_identity: 'Female', rsvp: 'Yes', meal_preference: 'Vegetarian', single: true, groups: ['Friends'], hobbies: ['reading', 'yoga'], languages: ['English', 'Spanish'], location: 'New York', diet_choices: ['vegetarian', 'gluten-free'], must_with: ['Bob'] },
  { ...createDefaultGuest('Bob'), id: '2', age: 31, gender_identity: 'Male', rsvp: 'Yes', meal_preference: 'Chicken', single: false, groups: ['Friends'], hobbies: ['reading', 'yoga'], languages: ['English'], location: 'New York', must_with: ['Alice'] },
  { ...createDefaultGuest('Carol'), id: '3', age: 27, gender_identity: 'Female', rsvp: 'Yes', meal_preference: 'Fish', single: true, groups: ['Family'], hobbies: ['music', 'travel'], languages: ['French', 'English'], location: 'Paris', diet_choices: ['vegan'], forced_table: 'Table 2' },
  { ...createDefaultGuest('David'), id: '4', age: 35, gender_identity: 'Male', rsvp: 'Yes', meal_preference: 'Beef', single: false, groups: ['Work'], hobbies: ['golf', 'cooking'], languages: ['English', 'German'], location: 'Berlin' },
  { ...createDefaultGuest('Eve'), id: '5', age: 28, gender_identity: 'Female', rsvp: 'Yes', meal_preference: 'Vegetarian', single: true, groups: ['Friends'], hobbies: ['reading', 'music'], languages: ['English'], location: 'New York', diet_choices: ['vegetarian'] },
];

const SAMPLE_TABLES: Table[] = [
  { name: 'Table 1', capacity: 3, tags: ['Friends'] },
  { name: 'Table 2', capacity: 3, tags: ['Family'] },
];

const SAMPLE_RELATIONSHIPS: Relationship[] = [
  { guest1_id: '1', guest2_id: '2', relationship: 'friend', strength: 3, notes: 'Alice and Bob are friends' },
  { guest1_id: '1', guest2_id: '3', relationship: 'know', strength: 2, notes: 'Alice knows Carol' },
  { guest1_id: '2', guest2_id: '3', relationship: 'neutral', strength: 0, notes: 'Bob and Carol are neutral' },
  { guest1_id: '4', guest2_id: '5', relationship: 'married', strength: 5, notes: 'David and Eve are married' },
];

// ---- Template download helpers ----

const TEMPLATES: Record<string, string> = {
  guests: [
    'id,name,age,gender_identity,rsvp,meal_preference,single,groups,hobbies,languages,must_with,must_separate,forced_table',
    'g1,Alice Johnson,32,female,yes,chicken,false,family,hiking|cooking,English,,Bob Smith,',
    'g2,Bob Smith,35,male,yes,vegetarian,false,family,hiking|music,English,Alice Johnson,,',
    'g3,Carol White,28,female,yes,fish,true,friends,painting|yoga,English|Spanish,,',
    'g4,David Lee,45,male,yes,chicken,false,work,golf|travel,English|Mandarin,,,Head Table',
    'g5,Emma Brown,31,female,yes,vegan,true,friends,yoga|reading,English|French,,David Lee,',
  ].join('\n'),

  tables: [
    'name,capacity,tags',
    'Head Table,10,vip|family',
    'Table 2,8,friends',
    'Table 3,8,work',
    'Table 4,6,family',
    'Table 5,8,',
  ].join('\n'),

  relationships: [
    'guest1_id,guest2_id,relationship,strength,notes',
    'g1,g2,best friend,5,Childhood friends',
    'g1,g3,friend,3,Met at college',
    'g2,g4,colleague,2,Work together',
    'g3,g5,friend,3,Yoga class',
    'g4,g5,avoid,-3,Had a disagreement last year',
  ].join('\n'),
};

function downloadTemplate(type: 'guests' | 'tables' | 'relationships') {
  const blob = new Blob([TEMPLATES[type]], { type: 'text/csv' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `${type}_template.csv`;
  a.click();
  URL.revokeObjectURL(url);
}

interface OptionsPanelProps {
  onClose?: () => void;
}

export const OptionsPanel: React.FC<OptionsPanelProps> = ({ onClose }) => {
  const options = useAppStore((s) => s.options);
  const setOptions = useAppStore((s) => s.setOptions);
  const undo = useAppStore((s) => s.undo);
  const redo = useAppStore((s) => s.redo);
  const undoStack = useAppStore((s) => s.undoStack);
  const redoStack = useAppStore((s) => s.redoStack);
  const solve = useAppStore((s) => s.solve);
  const isLoading = useAppStore((s) => s.isLoading);
  const error = useAppStore((s) => s.error);
  const setGuests = useAppStore((s) => s.setGuests);
  const setTables = useAppStore((s) => s.setTables);
  const setRelationships = useAppStore((s) => s.setRelationships);
  const clearAssignments = useAppStore((s) => s.clearAssignments);
  const guests = useAppStore((s) => s.guests);
  const tables = useAppStore((s) => s.tables);

  const guestFileRef = useRef<HTMLInputElement>(null);
  const tableFileRef = useRef<HTMLInputElement>(null);
  const relFileRef = useRef<HTMLInputElement>(null);

  const [importStatus, setImportStatus] = useState('');
  const [showRandomizer, setShowRandomizer] = useState(false);

  const handleToggle = (key: keyof typeof options) => {
    const val = options[key];
    if (typeof val === 'boolean') {
      setOptions({ ...options, [key]: !val });
    }
  };

  // ---- CSV Import Handlers ----
  const handleGuestCSV = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const text = await file.text();
    const rows = parseCSV(text);
    const parsed: Guest[] = rows.map((r) => ({
      ...createDefaultGuest(r.name || 'Unknown'),
      id: r.id || `guest-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`,
      name: r.name || 'Unknown',
      age: parseInt(r.age) || 0,
      gender_identity: r.gender_identity || '',
      rsvp: r.rsvp || '',
      meal_preference: r.meal_preference || '',
      single: r.single?.toLowerCase() === 'true',
      interested_in: parsePipe(r.interested_in),
      plus_one: r.plus_one?.toLowerCase() === 'true',
      sit_with_partner: r.sit_with_partner?.toLowerCase() !== 'false',
      min_known: parseInt(r.min_known) || 0,
      min_unknown: parseInt(r.min_unknown) || 0,
      weight: parseInt(r.weight) || 1,
      must_with: parsePipe(r.must_with),
      must_separate: parsePipe(r.must_separate),
      groups: parsePipe(r.groups),
      hobbies: parsePipe(r.hobbies),
      languages: parsePipe(r.languages),
      relationship_status: r.relationship_status || '',
      forced_table: r.forced_table || '',
      location: r.location || '',
      diet_choices: parsePipe(r.diet_choices),
      partner: r.partner || '',
    }));
    setGuests(parsed);
    clearAssignments();
    setImportStatus(`Imported ${parsed.length} guests`);
    e.target.value = '';
  };

  const handleTableCSV = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const text = await file.text();
    const rows = parseCSV(text);
    const parsed: Table[] = rows.map((r, idx) => ({
      name: r.name || `Table ${idx + 1}`,
      capacity: parseInt(r.capacity) || 8,
      tags: parsePipe(r.tags),
    }));
    setTables(parsed);
    clearAssignments();
    setImportStatus(`Imported ${parsed.length} tables`);
    e.target.value = '';
  };

  const handleRelCSV = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const text = await file.text();
    const rows = parseCSV(text);
    const parsed: Relationship[] = rows.map((r) => ({
      guest1_id: r.guest1_id || '',
      guest2_id: r.guest2_id || '',
      relationship: r.relationship || 'neutral',
      strength: parseInt(r.strength) || 0,
      notes: r.notes || '',
    }));
    setRelationships(parsed);
    setImportStatus(`Imported ${parsed.length} relationships`);
    e.target.value = '';
  };

  return (
    <>
    <div className="w-64 bg-white border-r border-gray-200 overflow-y-auto flex flex-col h-full">
      {/* Header */}
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <h1 className="text-lg font-bold text-gray-900">WeddingTableMatch</h1>
          {onClose && (
            <button
              onClick={onClose}
              className="lg:hidden p-1 rounded text-gray-400 hover:text-gray-600 hover:bg-gray-100 cursor-pointer transition-colors"
              aria-label="Close menu"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          )}
        </div>
        <p className="text-xs text-gray-500 mt-1">
          {guests.length} guests, {tables.length} tables
        </p>
        <button
          onClick={() => setShowRandomizer(true)}
          className="mt-2 w-full px-3 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg text-xs font-semibold transition-colors cursor-pointer text-left flex items-center gap-2"
        >
          <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          Generate random wedding
        </button>
        <button
          onClick={() => {
            setGuests(SAMPLE_GUESTS);
            setTables(SAMPLE_TABLES);
            setRelationships(SAMPLE_RELATIONSHIPS);
            clearAssignments();
            setImportStatus('Sample data loaded');
          }}
          className="w-full px-3 py-1.5 bg-gray-50 hover:bg-gray-100 text-gray-500 rounded-lg text-xs transition-colors cursor-pointer text-left"
        >
          Load 5-guest sample
        </button>
      </div>

      {/* CSV Import */}
      <div className="p-4 border-b border-gray-200">
        <h3 className="text-sm font-semibold text-gray-700 mb-3">Import Data</h3>
        <div className="space-y-2">
          <input ref={guestFileRef} type="file" accept=".csv" onChange={handleGuestCSV} className="hidden" />
          <button
            onClick={() => guestFileRef.current?.click()}
            className="w-full px-3 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg text-sm transition-colors text-left"
          >
            Upload Guests CSV
          </button>
          <button
            onClick={() => downloadTemplate('guests')}
            className="text-xs text-blue-500 hover:text-blue-700 px-1 cursor-pointer transition-colors"
          >
            Download template
          </button>

          <input ref={tableFileRef} type="file" accept=".csv" onChange={handleTableCSV} className="hidden" />
          <button
            onClick={() => tableFileRef.current?.click()}
            className="w-full px-3 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg text-sm transition-colors text-left"
          >
            Upload Tables CSV
          </button>
          <button
            onClick={() => downloadTemplate('tables')}
            className="text-xs text-blue-500 hover:text-blue-700 px-1 cursor-pointer transition-colors"
          >
            Download template
          </button>

          <input ref={relFileRef} type="file" accept=".csv" onChange={handleRelCSV} className="hidden" />
          <button
            onClick={() => relFileRef.current?.click()}
            className="w-full px-3 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg text-sm transition-colors text-left"
          >
            Upload Relationships CSV
          </button>
          <button
            onClick={() => downloadTemplate('relationships')}
            className="text-xs text-blue-500 hover:text-blue-700 px-1 cursor-pointer transition-colors"
          >
            Download template
          </button>

          {importStatus && (
            <p className="text-xs text-green-700 mt-1">{importStatus}</p>
          )}
        </div>
      </div>

      {/* Solver Options */}
      <div className="p-4 border-b border-gray-200">
        <h3 className="text-sm font-semibold text-gray-700 mb-3">Solver Settings</h3>
        <div className="space-y-2">
          {([
            ['maximize_known', 'Maximize Known'],
            ['group_singles', 'Group Singles'],
            ['group_by_meal_preference', 'Group by Meal'],
            ['equalize_tables', 'Equalize Tables'],
            ['match_hobbies', 'Match Hobbies'],
            ['match_languages', 'Match Languages'],
            ['match_age', 'Match Age'],
            ['match_relationship_status', 'Match Rel. Status'],
            ['match_location', 'Match Location'],
            ['match_diet', 'Match Diet'],
            ['respect_forced_table', 'Respect Forced Table'],
          ] as [keyof typeof options, string][]).map(([key, label]) => (
            <label key={key} className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={options[key] as boolean}
                onChange={() => handleToggle(key)}
                className="w-3.5 h-3.5 rounded border-gray-300 cursor-pointer"
              />
              <span className="text-xs text-gray-700">{label}</span>
            </label>
          ))}
        </div>
      </div>

      {/* Action Buttons */}
      <div className="p-4 border-b border-gray-200">
        <div className="space-y-2">
          <button
            onClick={() => solve()}
            disabled={isLoading}
            className="w-full px-4 py-2 bg-blue-500 hover:bg-blue-600 disabled:bg-gray-400 text-white rounded-lg font-medium text-sm transition-colors"
          >
            {isLoading ? 'Solving...' : 'Auto Solve'}
          </button>

          <div className="flex gap-2">
            <button
              onClick={undo}
              disabled={undoStack.length === 0}
              className="flex-1 px-3 py-2 bg-gray-200 hover:bg-gray-300 disabled:bg-gray-100 disabled:text-gray-400 text-gray-700 rounded-lg font-medium text-sm transition-colors"
            >
              Undo
            </button>
            <button
              onClick={redo}
              disabled={redoStack.length === 0}
              className="flex-1 px-3 py-2 bg-gray-200 hover:bg-gray-300 disabled:bg-gray-100 disabled:text-gray-400 text-gray-700 rounded-lg font-medium text-sm transition-colors"
            >
              Redo
            </button>
          </div>
        </div>
      </div>

      {/* Error display */}
      {error && (
        <div className="p-4 bg-red-50 border-b border-red-200">
          <p className="text-xs text-red-700">{error}</p>
        </div>
      )}

      {/* Tips */}
      <div className="p-4 flex-1 text-xs text-gray-500 space-y-1">
        <p className="font-semibold text-gray-600">Tips:</p>
        <ul className="space-y-1 list-disc list-inside">
          <li>Upload CSVs to import data</li>
          <li>Drag guests between tables</li>
          <li>Use Auto Solve to optimize</li>
          <li>Undo/Redo to revert changes</li>
        </ul>
      </div>
    </div>

    {showRandomizer && <RandomizerModal onClose={() => setShowRandomizer(false)} />}
    </>
  );
};
