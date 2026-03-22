import React, { useState } from 'react';
import { useAppStore } from '../../store';
import { Guest, Table, Relationship, TableShape, createDefaultGuest } from '../../types';

// ---- Name pools ----
const FM = ['James','John','Robert','Michael','William','David','Richard','Joseph','Thomas','Charles','Christopher','Daniel','Matthew','Anthony','Mark','Paul','Steven','Andrew','Kevin','Brian','George','Ryan','Jason','Gary','Eric','Jeffrey','Brandon','Benjamin','Samuel','Frank','Patrick','Scott','Jonathan','Timothy','Larry','Justin','Raymond','Gregory','Jerry','Dennis'];
const FF = ['Mary','Patricia','Jennifer','Linda','Barbara','Elizabeth','Susan','Jessica','Sarah','Karen','Emma','Olivia','Ava','Isabella','Sophia','Charlotte','Amelia','Harper','Evelyn','Claire','Grace','Lily','Natalie','Samantha','Hannah','Lauren','Rachel','Victoria','Chloe','Madison','Abigail','Emily','Ella','Katherine','Amanda','Melissa','Stephanie','Rebecca','Angela','Brittany'];
const FL = ['Smith','Johnson','Williams','Brown','Jones','Garcia','Miller','Davis','Rodriguez','Martinez','Wilson','Anderson','Taylor','Moore','Jackson','Martin','Lee','Thompson','White','Harris','Sanchez','Clark','Lewis','Robinson','Walker','Hall','Young','Allen','King','Wright','Scott','Torres','Nguyen','Hill','Flores','Green','Adams','Nelson','Baker','Carter'];
const HOBBIES_LIST = ['hiking','reading','cooking','travel','photography','music','yoga','golf','painting','gardening','cycling','dancing','swimming','tennis','wine tasting','skiing','running','birdwatching','pottery','sailing'];
const LANG_LIST = ['Spanish','French','German','Italian','Mandarin','Portuguese','Japanese','Arabic','Hindi','Korean','Polish','Greek','Russian','Swedish'];
const MEAL_OPTS = ['chicken','fish','beef','vegetarian','vegan'];
const DIET_OPTS = ['gluten-free','dairy-free','nut-free','kosher','halal'];

type ShapeStyle = 'round' | 'rect' | 'mixed';

interface Config {
  guestCount: number;
  tableCapacity: number;
  shapeStyle: ShapeStyle;
  includeHeadTable: boolean;
  couplePercent: number;
  conflictPairs: number;
  dietaryRestrictions: boolean;
  multilingual: boolean;
  singlesMixing: boolean;
  includeExes: boolean;
  divorcedParents: boolean;
}

// ---- Helpers ----
function pick<T>(arr: T[]): T { return arr[Math.floor(Math.random() * arr.length)]; }
function pickN<T>(arr: T[], n: number): T[] { return [...arr].sort(() => Math.random() - 0.5).slice(0, Math.min(n, arr.length)); }
function rand(a: number, b: number) { return Math.floor(Math.random() * (b - a + 1)) + a; }
function shuffle<T>(arr: T[]): T[] { return [...arr].sort(() => Math.random() - 0.5); }

// ---- Data generator ----
function generateData(config: Config): { guests: Guest[]; tables: Table[]; relationships: Relationship[] } {
  const guests: Guest[] = [];
  const relationships: Relationship[] = [];
  const usedNames = new Set<string>();
  const relSet = new Set<string>();
  let idCounter = 1;

  function uid() { return `g${idCounter++}`; }

  function uniqueName(pool: string[]): string {
    const shuffled = shuffle(pool);
    for (const fn of shuffled) {
      for (let t = 0; t < 6; t++) {
        const name = `${fn} ${pick(FL)}`;
        if (!usedNames.has(name)) { usedNames.add(name); return name; }
      }
    }
    const fallback = `Guest ${idCounter}`;
    usedNames.add(fallback);
    return fallback;
  }

  function addRel(id1: string, id2: string, rel: string, strength: number, notes = '') {
    const key = [id1, id2].sort().join('|');
    if (relSet.has(key)) return;
    relSet.add(key);
    relationships.push({ guest1_id: id1, guest2_id: id2, relationship: rel, strength, notes });
  }

  function makeGuest(name: string, overrides: Partial<Guest> = {}): Guest {
    const isFemale = Math.random() < 0.5;
    return {
      ...createDefaultGuest(name),
      id: uid(),
      name,
      age: rand(22, 72),
      gender_identity: isFemale ? 'female' : 'male',
      rsvp: 'yes',
      meal_preference: pick(MEAL_OPTS),
      diet_choices: config.dietaryRestrictions && Math.random() < 0.25
        ? pickN(DIET_OPTS, rand(1, 2))
        : [],
      hobbies: pickN(HOBBIES_LIST, rand(1, 3)),
      languages: config.multilingual && Math.random() < 0.2
        ? ['English', pick(LANG_LIST)]
        : ['English'],
      single: false,
      ...overrides,
    };
  }

  // Group buckets: group label → guest IDs
  const groupMap: Record<string, string[]> = {
    bride_family: [],
    groom_family: [],
    college_friends: [],
    work_colleagues: [],
    childhood_friends: [],
    neighbors: [],
  };

  // ---- Bride & Groom ----
  const brideName = uniqueName(FF);
  const groomName = uniqueName(FM);
  const bride = makeGuest(brideName, {
    groups: ['bride_family'],
    forced_table: config.includeHeadTable ? 'Head Table' : '',
    must_with: [groomName],
    age: rand(25, 38),
    gender_identity: 'female',
  });
  const groom = makeGuest(groomName, {
    groups: ['groom_family'],
    forced_table: config.includeHeadTable ? 'Head Table' : '',
    must_with: [brideName],
    age: rand(25, 40),
    gender_identity: 'male',
  });
  guests.push(bride, groom);
  groupMap.bride_family.push(bride.id);
  groupMap.groom_family.push(groom.id);
  addRel(bride.id, groom.id, 'married', 5, 'The couple — keep together');

  // ---- Distribute remaining guests across groups ----
  const remaining = config.guestCount - 2;
  const dist = {
    bride_family: Math.round(remaining * 0.20),
    groom_family: Math.round(remaining * 0.20),
    college_friends: Math.round(remaining * 0.18),
    work_colleagues: Math.round(remaining * 0.18),
    childhood_friends: Math.round(remaining * 0.14),
    neighbors: 0,
  };
  dist.neighbors = Math.max(0, remaining - Object.values(dist).reduce((a, b) => a + b, 0));

  for (const [group, size] of Object.entries(dist)) {
    for (let i = 0; i < size; i++) {
      const isFemale = Math.random() < 0.5;
      const name = uniqueName(isFemale ? FF : FM);
      const g = makeGuest(name, { groups: [group] });
      guests.push(g);
      groupMap[group].push(g.id);
    }
  }

  // ---- Head table: force a few close family members ----
  if (config.includeHeadTable) {
    let headAdded = 0;
    for (const id of shuffle([...groupMap.bride_family, ...groupMap.groom_family])) {
      if (headAdded >= 6) break;
      const g = guests.find(g => g.id === id && g.id !== bride.id && g.id !== groom.id);
      if (g && !g.forced_table) {
        g.forced_table = 'Head Table';
        headAdded++;
      }
    }
  }

  // ---- Couples ----
  const coupleTarget = Math.floor(config.guestCount * (config.couplePercent / 100) / 2);
  const couplePool = shuffle(
    guests
      .filter(g => g.id !== bride.id && g.id !== groom.id)
      .map(g => g.id)
  );
  const paired = new Set<string>([bride.id, groom.id]);

  for (let i = 0; i < coupleTarget && couplePool.length >= 2; ) {
    const id1 = couplePool.shift()!;
    const id2 = couplePool.shift()!;
    if (paired.has(id1) || paired.has(id2)) continue;
    paired.add(id1);
    paired.add(id2);
    const g1 = guests.find(g => g.id === id1)!;
    const g2 = guests.find(g => g.id === id2)!;
    g1.partner = g2.name;
    g2.partner = g1.name;
    g1.must_with = [g2.name];
    g2.must_with = [g1.name];
    g1.single = false;
    g2.single = false;
    addRel(id1, id2, 'partner', 5, 'Couple — seat together');
    i++;
  }

  // ---- Singles wanting to mingle ----
  if (config.singlesMixing) {
    const unpaired = guests.filter(g => !paired.has(g.id));
    pickN(unpaired, Math.ceil(unpaired.length * 0.45)).forEach(g => {
      g.single = true;
    });
  }

  // ---- Intra-group relationships ----
  for (const [group, ids] of Object.entries(groupMap)) {
    const relType = group.includes('family') ? 'family'
                  : group.includes('work') ? 'colleague'
                  : 'friend';
    for (let i = 0; i < ids.length; i++) {
      for (let j = i + 1; j < ids.length; j++) {
        // Full coverage for family, sampled for other groups
        if (relType === 'family' || Math.random() < 0.6) {
          addRel(ids[i], ids[j], relType, rand(2, 4));
        }
      }
    }
  }

  // ---- Bride & groom know their own family well ----
  groupMap.bride_family.forEach(id => {
    if (id !== bride.id) addRel(bride.id, id, 'family', rand(3, 5));
  });
  groupMap.groom_family.forEach(id => {
    if (id !== groom.id) addRel(groom.id, id, 'family', rand(3, 5));
  });

  // ---- Cross-group: shared friends between families ----
  const bFam = groupMap.bride_family.slice(0, 3);
  const gFam = groupMap.groom_family.slice(0, 3);
  bFam.forEach(id1 => gFam.forEach(id2 => {
    if (Math.random() < 0.4) addRel(id1, id2, 'know', rand(1, 3), 'Met through the couple');
  }));

  // ---- Conflict pairs ----
  const conflictCandidates = shuffle(
    guests.filter(g => g.id !== bride.id && g.id !== groom.id).map(g => g.id)
  );
  let conflictsAdded = 0;
  let ci = 0;
  while (conflictsAdded < config.conflictPairs && ci + 1 < conflictCandidates.length) {
    const id1 = conflictCandidates[ci++];
    const id2 = conflictCandidates[ci++];
    const g1 = guests.find(g => g.id === id1)!;
    const g2 = guests.find(g => g.id === id2)!;
    // Skip if they're a couple
    if (g1?.partner === g2?.name) continue;
    g1.must_separate = [...(g1.must_separate || []), g2.name];
    g2.must_separate = [...(g2.must_separate || []), g1.name];
    addRel(id1, id2, 'conflict', -rand(3, 5), 'Keep apart');
    conflictsAdded++;
  }

  // ---- Ex-partners edge case ----
  if (config.includeExes) {
    const singles = guests.filter(g => !paired.has(g.id) && g.id !== bride.id && g.id !== groom.id);
    if (singles.length >= 2) {
      const [ex1, ex2] = shuffle(singles);
      ex1.must_separate = [...(ex1.must_separate || []), ex2.name];
      ex2.must_separate = [...(ex2.must_separate || []), ex1.name];
      addRel(ex1.id, ex2.id, 'ex-partner', -rand(2, 4), 'Exes — definitely keep apart');
    }
  }

  // ---- Divorced parents edge case ----
  if (config.divorcedParents) {
    const candidates = shuffle([
      ...groupMap.bride_family.filter(id => id !== bride.id),
      ...groupMap.groom_family.filter(id => id !== groom.id),
    ]);
    if (candidates.length >= 2) {
      const [p1id, p2id] = candidates;
      const p1 = guests.find(g => g.id === p1id)!;
      const p2 = guests.find(g => g.id === p2id)!;
      if (p1?.partner !== p2?.name) {
        p1.must_separate = [...(p1.must_separate || []), p2.name];
        p2.must_separate = [...(p2.must_separate || []), p1.name];
        addRel(p1id, p2id, 'divorced', -3, "Divorced — seat at opposite ends");
      }
    }
  }

  // ---- Tables ----
  const headTableGuests = guests.filter(g => g.forced_table === 'Head Table').length;
  const regularGuests = config.guestCount - headTableGuests;
  const regularTableCount = Math.max(1, Math.ceil(regularGuests / config.tableCapacity));

  const tables: Table[] = [];

  if (config.includeHeadTable) {
    tables.push({
      name: 'Head Table',
      capacity: Math.max(headTableGuests + 2, 8),
      tags: ['vip'],
      shape: 'long',
    });
  }

  for (let i = 1; i <= regularTableCount; i++) {
    let shape: TableShape = 'round';
    if (config.shapeStyle === 'rect') shape = 'rect';
    else if (config.shapeStyle === 'mixed') shape = pick(['round', 'round', 'rect'] as TableShape[]);
    tables.push({ name: `Table ${i}`, capacity: config.tableCapacity, tags: [], shape });
  }

  return { guests, tables, relationships };
}

// ---- Sub-components ----

const SliderField: React.FC<{
  label: string;
  value: number;
  min: number;
  max: number;
  step?: number;
  suffix?: string;
  onChange: (v: number) => void;
}> = ({ label, value, min, max, step = 1, suffix = '', onChange }) => (
  <div>
    <div className="flex items-center justify-between mb-1">
      <label className="text-xs text-gray-600">{label}</label>
      <span className="text-xs font-semibold text-gray-800 tabular-nums">{value}{suffix}</span>
    </div>
    <input
      type="range"
      min={min}
      max={max}
      step={step}
      value={value}
      onChange={e => onChange(Number(e.target.value))}
      className="w-full h-1.5 rounded-full appearance-none bg-gray-200 accent-blue-500 cursor-pointer"
    />
    <div className="flex justify-between text-[10px] text-gray-400 mt-0.5">
      <span>{min}</span>
      <span>{max}</span>
    </div>
  </div>
);

const ToggleField: React.FC<{
  label: string;
  hint?: string;
  checked: boolean;
  onChange: (v: boolean) => void;
}> = ({ label, hint, checked, onChange }) => (
  <label className="flex items-start gap-3 cursor-pointer group">
    <div className="mt-0.5 shrink-0">
      <div
        onClick={() => onChange(!checked)}
        className={`w-8 h-4 rounded-full relative transition-colors cursor-pointer ${checked ? 'bg-blue-500' : 'bg-gray-200'}`}
      >
        <div className={`absolute top-0.5 w-3 h-3 rounded-full bg-white shadow transition-transform ${checked ? 'translate-x-4' : 'translate-x-0.5'}`} />
      </div>
    </div>
    <div>
      <p className="text-xs font-medium text-gray-700">{label}</p>
      {hint && <p className="text-[11px] text-gray-400 mt-0.5">{hint}</p>}
    </div>
  </label>
);

// ---- Main Modal ----

export const RandomizerModal: React.FC<{ onClose: () => void }> = ({ onClose }) => {
  const setGuests = useAppStore(s => s.setGuests);
  const setTables = useAppStore(s => s.setTables);
  const setRelationships = useAppStore(s => s.setRelationships);
  const clearAssignments = useAppStore(s => s.clearAssignments);

  const [config, setConfig] = useState<Config>({
    guestCount: 60,
    tableCapacity: 8,
    shapeStyle: 'round',
    includeHeadTable: true,
    couplePercent: 40,
    conflictPairs: 2,
    dietaryRestrictions: true,
    multilingual: true,
    singlesMixing: true,
    includeExes: true,
    divorcedParents: true,
  });

  function set<K extends keyof Config>(key: K, value: Config[K]) {
    setConfig(c => ({ ...c, [key]: value }));
  }

  const headTableGuests = config.includeHeadTable ? Math.min(8, Math.round(config.guestCount * 0.12)) : 0;
  const regularGuests = config.guestCount - headTableGuests;
  const tableCount = (config.includeHeadTable ? 1 : 0) + Math.max(1, Math.ceil(regularGuests / config.tableCapacity));
  const coupleCount = Math.floor(config.guestCount * (config.couplePercent / 100) / 2);
  const relEstimate = Math.round(config.guestCount * 2.5);

  const handleGenerate = () => {
    const { guests, tables, relationships } = generateData(config);
    setGuests(guests);
    setTables(tables);
    setRelationships(relationships);
    clearAssignments();
    onClose();
  };

  return (
    <div
      className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4"
      onClick={e => { if (e.target === e.currentTarget) onClose(); }}
    >
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md max-h-[92vh] flex flex-col">
        {/* Header */}
        <div className="px-6 py-5 border-b border-gray-100 flex items-start justify-between shrink-0">
          <div>
            <h2 className="text-lg font-semibold text-gray-900">Generate Wedding Data</h2>
            <p className="text-xs text-gray-400 mt-1">
              ~{config.guestCount} guests · ~{tableCount} tables · ~{coupleCount} couples · ~{relEstimate} relationships
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg cursor-pointer transition-colors ml-4 shrink-0"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Body */}
        <div className="px-6 py-5 space-y-6 overflow-y-auto flex-1">
          {/* Wedding Size */}
          <section>
            <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">Wedding Size</h3>
            <div className="space-y-4">
              <SliderField
                label="Total guests"
                value={config.guestCount}
                min={10}
                max={200}
                step={5}
                onChange={v => set('guestCount', v)}
              />
              <SliderField
                label="Seats per table"
                value={config.tableCapacity}
                min={4}
                max={16}
                onChange={v => set('tableCapacity', v)}
              />
            </div>
          </section>

          {/* Table Setup */}
          <section>
            <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">Table Setup</h3>
            <div className="space-y-3">
              <div>
                <p className="text-xs text-gray-600 mb-2">Table shape</p>
                <div className="flex gap-2">
                  {(['round', 'rect', 'mixed'] as ShapeStyle[]).map(s => (
                    <button
                      key={s}
                      onClick={() => set('shapeStyle', s)}
                      className={`flex-1 py-1.5 text-xs rounded-lg border transition-colors cursor-pointer font-medium ${
                        config.shapeStyle === s
                          ? 'bg-blue-500 text-white border-blue-500'
                          : 'bg-white text-gray-600 border-gray-200 hover:border-gray-300'
                      }`}
                    >
                      {s === 'round' ? 'All Round' : s === 'rect' ? 'All Square' : 'Mixed'}
                    </button>
                  ))}
                </div>
              </div>
              <ToggleField
                label="Head table"
                hint="Long table for couple + close family, forced seating"
                checked={config.includeHeadTable}
                onChange={v => set('includeHeadTable', v)}
              />
            </div>
          </section>

          {/* Guest Mix */}
          <section>
            <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">Guest Mix</h3>
            <div className="space-y-4">
              <SliderField
                label="Couples"
                value={config.couplePercent}
                min={0}
                max={70}
                step={5}
                suffix="% of guests"
                onChange={v => set('couplePercent', v)}
              />
              <SliderField
                label="Conflict pairs"
                value={config.conflictPairs}
                min={0}
                max={8}
                onChange={v => set('conflictPairs', v)}
              />
            </div>
          </section>

          {/* Edge Cases */}
          <section>
            <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">Edge Cases</h3>
            <div className="space-y-3">
              <ToggleField
                label="Dietary restrictions"
                hint="~25% of guests have special dietary needs"
                checked={config.dietaryRestrictions}
                onChange={v => set('dietaryRestrictions', v)}
              />
              <ToggleField
                label="Multilingual guests"
                hint="~20% of guests primarily speak another language"
                checked={config.multilingual}
                onChange={v => set('multilingual', v)}
              />
              <ToggleField
                label="Singles looking to mingle"
                hint="~45% of unpartnered guests flagged as singles"
                checked={config.singlesMixing}
                onChange={v => set('singlesMixing', v)}
              />
              <ToggleField
                label="Ex-partners present"
                hint="One awkward ex-couple that must be separated"
                checked={config.includeExes}
                onChange={v => set('includeExes', v)}
              />
              <ToggleField
                label="Divorced parents"
                hint="A divorced parent pair from bride or groom's side"
                checked={config.divorcedParents}
                onChange={v => set('divorcedParents', v)}
              />
            </div>
          </section>
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-gray-100 flex gap-3 shrink-0">
          <button
            onClick={onClose}
            className="flex-1 py-2.5 text-sm text-gray-600 bg-gray-100 hover:bg-gray-200 rounded-xl cursor-pointer transition-colors font-medium"
          >
            Cancel
          </button>
          <button
            onClick={handleGenerate}
            className="flex-1 py-2.5 text-sm font-semibold text-white bg-blue-500 hover:bg-blue-600 rounded-xl cursor-pointer transition-colors"
          >
            Generate Wedding
          </button>
        </div>
      </div>
    </div>
  );
};
