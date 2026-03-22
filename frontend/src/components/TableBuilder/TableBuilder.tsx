import React, { useState } from 'react';
import { useAppStore } from '../../store';
import { Table, TableShape } from '../../types';

// ---- Wedding table format presets ----
interface TablePreset {
  label: string;
  hint: string;
  capacity: number;
  shape: TableShape;
  tags: string[];
  namePrefix: string;
}

const TABLE_PRESETS: TablePreset[] = [
  { label: 'Sweetheart', hint: '2 · round', capacity: 2, shape: 'round', tags: ['couple'], namePrefix: 'Sweetheart Table' },
  { label: 'Head Table', hint: '12 · long', capacity: 12, shape: 'long', tags: ['vip', 'wedding party'], namePrefix: 'Head Table' },
  { label: 'Round 8', hint: '8 · round', capacity: 8, shape: 'round', tags: [], namePrefix: 'Table' },
  { label: 'Round 10', hint: '10 · round', capacity: 10, shape: 'round', tags: [], namePrefix: 'Table' },
  { label: 'Farm Table', hint: '14 · long', capacity: 14, shape: 'long', tags: ['harvest'], namePrefix: 'Farm Table' },
  { label: 'Cocktail', hint: '4 · round', capacity: 4, shape: 'round', tags: ['cocktail'], namePrefix: 'Cocktail' },
  { label: 'Rectangular', hint: '8 · rect', capacity: 8, shape: 'rect', tags: [], namePrefix: 'Table' },
  { label: 'Kids Table', hint: '6 · round', capacity: 6, shape: 'round', tags: ['kids'], namePrefix: 'Kids Table' },
  { label: 'Family Style', hint: '16 · long', capacity: 16, shape: 'long', tags: ['family'], namePrefix: 'Family Table' },
  { label: 'VIP Round', hint: '10 · round', capacity: 10, shape: 'round', tags: ['vip'], namePrefix: 'VIP Table' },
];

// Shape icon SVGs
const ShapeIcon: React.FC<{ shape: TableShape; active: boolean; onClick: () => void }> = ({ shape, active, onClick }) => {
  const base = `p-1 rounded transition-colors cursor-pointer ${active ? 'bg-blue-100 text-blue-600' : 'text-gray-400 hover:text-gray-600 hover:bg-gray-100'}`;
  return (
    <button className={base} onClick={onClick} title={shape}>
      <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
        {shape === 'round' && <circle cx="12" cy="12" r="9" />}
        {shape === 'rect' && <rect x="3" y="5" width="18" height="14" rx="2" />}
        {shape === 'long' && <rect x="1" y="8" width="22" height="8" rx="2" />}
      </svg>
    </button>
  );
};

// ---- Individual Row ----

interface RowProps {
  table: Table;
  occupied: number;
  isDuplicate: boolean;
  onUpdate: (oldName: string, table: Table) => void;
  onDelete: (name: string) => void;
}

const TableRow: React.FC<RowProps> = ({ table, occupied, isDuplicate, onUpdate, onDelete }) => {
  const [name, setName] = useState(table.name);
  const [capacityStr, setCapacityStr] = useState(String(table.capacity));
  const [tags, setTags] = useState(table.tags.join(', '));

  const commit = () => {
    const trimmed = name.trim();
    if (!trimmed) {
      setName(table.name);
      return;
    }
    const cap = Math.max(1, parseInt(capacityStr) || 8);
    setCapacityStr(String(cap));
    const parsedTags = tags.split(',').map((s) => s.trim()).filter(Boolean);
    onUpdate(table.name, { ...table, name: trimmed, capacity: cap, tags: parsedTags });
  };

  const setShape = (shape: TableShape) => {
    onUpdate(table.name, { ...table, shape });
  };

  const cap = parseInt(capacityStr) || 8;
  const pct = Math.min(1, occupied / Math.max(1, cap));
  const barColor = pct >= 1 ? 'bg-red-400' : pct > 0.75 ? 'bg-amber-400' : 'bg-emerald-400';

  return (
    <div className="flex items-center gap-3 px-4 py-3 border-b border-gray-100 hover:bg-gray-50/70 group transition-colors">
      {/* Name */}
      <div className="flex-1 min-w-0 min-w-[120px]">
        <input
          value={name}
          onChange={(e) => setName(e.target.value)}
          onBlur={commit}
          onKeyDown={(e) => { if (e.key === 'Enter') e.currentTarget.blur(); }}
          className={`w-full text-sm font-medium text-gray-900 bg-transparent border rounded px-2 py-1 transition-colors focus:outline-none ${
            isDuplicate
              ? 'border-red-300 bg-red-50'
              : 'border-transparent hover:border-gray-300 focus:border-blue-400'
          }`}
        />
        {isDuplicate && (
          <p className="text-xs text-red-500 mt-0.5 px-2">Name already used</p>
        )}
      </div>

      {/* Capacity */}
      <input
        type="number"
        min={1}
        max={99}
        value={capacityStr}
        onChange={(e) => setCapacityStr(e.target.value)}
        onBlur={commit}
        onKeyDown={(e) => { if (e.key === 'Enter') e.currentTarget.blur(); }}
        className="w-16 text-sm text-center text-gray-700 bg-transparent border border-transparent hover:border-gray-300 focus:border-blue-400 focus:outline-none rounded px-1 py-1 transition-colors shrink-0"
      />

      {/* Shape */}
      <div className="flex items-center gap-0.5 shrink-0">
        {(['round', 'rect', 'long'] as TableShape[]).map((s) => (
          <ShapeIcon key={s} shape={s} active={(table.shape ?? 'round') === s} onClick={() => setShape(s)} />
        ))}
      </div>

      {/* Tags */}
      <input
        value={tags}
        onChange={(e) => setTags(e.target.value)}
        onBlur={commit}
        onKeyDown={(e) => { if (e.key === 'Enter') e.currentTarget.blur(); }}
        placeholder="vip, family…"
        className="w-28 text-xs text-gray-600 bg-transparent border border-transparent hover:border-gray-300 focus:border-blue-400 focus:outline-none rounded px-2 py-1 transition-colors placeholder-gray-300 shrink-0"
      />

      {/* Occupancy */}
      <div className="flex items-center gap-2 w-24 shrink-0">
        <div className="flex-1 h-1.5 bg-gray-100 rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full transition-all duration-300 ${barColor}`}
            style={{ width: `${pct * 100}%` }}
          />
        </div>
        <span className="text-xs tabular-nums text-gray-500 w-8 text-right">
          {occupied}/{cap}
        </span>
      </div>

      {/* Delete */}
      <button
        onClick={() => onDelete(table.name)}
        className="p-1 text-gray-300 hover:text-red-500 opacity-0 group-hover:opacity-100 transition-all cursor-pointer rounded"
        title="Remove table"
      >
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
          />
        </svg>
      </button>
    </div>
  );
};

// ---- Main Component ----

export const TableBuilder: React.FC = () => {
  const tables = useAppStore((s) => s.tables);
  const guests = useAppStore((s) => s.guests);
  const assignments = useAppStore((s) => s.assignments);
  const addTable = useAppStore((s) => s.addTable);
  const removeTable = useAppStore((s) => s.removeTable);
  const updateTable = useAppStore((s) => s.updateTable);
  const setTables = useAppStore((s) => s.setTables);

  const [bulkCount, setBulkCount] = useState('5');
  const [bulkCapacity, setBulkCapacity] = useState('8');

  const occupancyMap = React.useMemo(() => {
    const map: Record<string, number> = {};
    for (const tableName of Object.values(assignments)) {
      map[tableName] = (map[tableName] || 0) + 1;
    }
    return map;
  }, [assignments]);

  const nameCount = React.useMemo(() => {
    const counts: Record<string, number> = {};
    for (const t of tables) counts[t.name] = (counts[t.name] || 0) + 1;
    return counts;
  }, [tables]);

  const totalCapacity = tables.reduce((sum, t) => sum + t.capacity, 0);
  const totalGuests = guests.length;
  const seatsAvailable = totalCapacity - totalGuests;

  const nextTableNum = () => {
    let num = tables.length + 1;
    const names = new Set(tables.map((t) => t.name));
    while (names.has(`Table ${num}`)) num++;
    return num;
  };

  const handleAdd = () => {
    addTable({ name: `Table ${nextTableNum()}`, capacity: 8, tags: [] });
  };

  const handleBulkAdd = () => {
    const count = Math.max(1, Math.min(50, parseInt(bulkCount) || 5));
    const cap = Math.max(1, parseInt(bulkCapacity) || 8);
    const newTables: Table[] = [];
    const existingNames = new Set(tables.map((t) => t.name));
    let num = tables.length + 1;
    for (let i = 0; i < count; i++) {
      while (existingNames.has(`Table ${num}`)) num++;
      const name = `Table ${num}`;
      existingNames.add(name);
      newTables.push({ name, capacity: cap, tags: [] });
      num++;
    }
    setTables([...tables, ...newTables]);
  };

  const handleAddPreset = (preset: TablePreset) => {
    const existingNames = new Set(tables.map((t) => t.name));
    // Find a unique name
    let name = preset.namePrefix;
    if (existingNames.has(name)) {
      let num = 2;
      while (existingNames.has(`${preset.namePrefix} ${num}`)) num++;
      name = `${preset.namePrefix} ${num}`;
    }
    addTable({ name, capacity: preset.capacity, shape: preset.shape, tags: preset.tags });
  };

  const handleDelete = (name: string) => {
    const occupied = occupancyMap[name] || 0;
    if (occupied > 0) {
      const ok = window.confirm(
        `"${name}" has ${occupied} guest${occupied !== 1 ? 's' : ''} assigned. Remove table and unassign them?`
      );
      if (!ok) return;
    }
    removeTable(name);
  };

  return (
    <div className="flex flex-col h-full bg-white">
      {/* Header */}
      <div className="px-6 pt-5 pb-4 border-b border-gray-200">
        {/* Title row */}
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-lg font-semibold text-gray-900">Tables</h2>
            <p className="text-xs text-gray-400 mt-0.5">
              {tables.length} {tables.length === 1 ? 'table' : 'tables'} · {totalCapacity} seats total
            </p>
          </div>
          <button
            onClick={handleAdd}
            className="flex items-center gap-2 bg-blue-500 hover:bg-blue-600 text-white text-sm font-medium px-4 py-2 rounded-lg cursor-pointer transition-colors"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            Add Table
          </button>
        </div>

        {/* Bulk add row */}
        <div className="flex items-center gap-2">
          <span className="text-xs text-gray-500">Bulk add:</span>
          <input
            type="number"
            min={1}
            max={50}
            value={bulkCount}
            onChange={(e) => setBulkCount(e.target.value)}
            className="w-14 text-sm text-center bg-white border border-gray-200 rounded-md px-2 py-1 focus:outline-none focus:border-blue-400 focus:ring-1 focus:ring-blue-100"
          />
          <span className="text-xs text-gray-500">tables,</span>
          <input
            type="number"
            min={1}
            max={99}
            value={bulkCapacity}
            onChange={(e) => setBulkCapacity(e.target.value)}
            className="w-14 text-sm text-center bg-white border border-gray-200 rounded-md px-2 py-1 focus:outline-none focus:border-blue-400 focus:ring-1 focus:ring-blue-100"
          />
          <span className="text-xs text-gray-500">seats each</span>
          <button
            onClick={handleBulkAdd}
            className="text-xs font-medium bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-md px-3 py-1.5 cursor-pointer transition-colors ml-1"
          >
            Add all
          </button>
        </div>
      </div>

      {/* Preset formats */}
      <div className="px-6 py-3 border-b border-gray-200 bg-gray-50">
        <p className="text-xs font-medium text-gray-400 uppercase tracking-wide mb-2">Standard Formats</p>
        <div className="flex flex-wrap gap-2">
          {TABLE_PRESETS.map((preset) => (
            <button
              key={preset.label}
              onClick={() => handleAddPreset(preset)}
              title={`Add ${preset.label} (${preset.hint})`}
              className="flex flex-col items-start px-2.5 py-1.5 bg-white border border-gray-200 hover:border-blue-300 hover:bg-blue-50 rounded-lg text-left transition-colors cursor-pointer group"
            >
              <span className="text-xs font-medium text-gray-700 group-hover:text-blue-600">{preset.label}</span>
              <span className="text-[10px] text-gray-400 group-hover:text-blue-400">{preset.hint}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Column headers */}
      {tables.length > 0 && (
        <div className="flex items-center gap-3 px-4 py-2 bg-gray-50 border-b border-gray-200 text-xs font-medium text-gray-400 uppercase tracking-wide">
          <span className="flex-1">Name</span>
          <span className="w-16 text-center">Seats</span>
          <span className="w-20">Shape</span>
          <span className="w-28">Tags</span>
          <span className="w-24">Occupancy</span>
          <span className="w-6" />
        </div>
      )}

      {/* Rows */}
      <div className="flex-1 overflow-y-auto">
        {tables.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full py-16 text-center">
            <svg
              className="w-12 h-12 text-gray-200 mb-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
                d="M3 10h18M3 14h18M10 10v10M14 10v10M5 6l7-3 7 3M5 6v14M19 6v14"
              />
            </svg>
            <p className="text-sm font-medium text-gray-400">No tables yet</p>
            <p className="text-xs text-gray-300 mt-1">
              Click "Add Table" or use bulk add above to get started
            </p>
          </div>
        ) : (
          tables.map((table) => (
            <TableRow
              key={table.name}
              table={table}
              occupied={occupancyMap[table.name] || 0}
              isDuplicate={(nameCount[table.name] || 0) > 1}
              onUpdate={updateTable}
              onDelete={handleDelete}
            />
          ))
        )}
      </div>

      {/* Footer */}
      {tables.length > 0 && (
        <div className="px-6 py-3 border-t border-gray-100 flex items-center gap-6 text-xs text-gray-500">
          <span>{tables.length} tables</span>
          <span>{totalCapacity} seats</span>
          <span>{totalGuests} guests</span>
          <span
            className={
              seatsAvailable < 0
                ? 'text-red-500 font-medium'
                : seatsAvailable === 0
                ? 'text-emerald-600 font-medium'
                : 'text-gray-500'
            }
          >
            {seatsAvailable < 0
              ? `${Math.abs(seatsAvailable)} seats short`
              : seatsAvailable === 0
              ? 'Exactly full'
              : `${seatsAvailable} seats available`}
          </span>
        </div>
      )}
    </div>
  );
};
