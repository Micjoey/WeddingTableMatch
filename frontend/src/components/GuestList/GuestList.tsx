import React, { useState, useMemo } from 'react';
import { useAppStore } from '../../store';
import { Guest, createDefaultGuest } from '../../types';
import { GuestEditModal } from './GuestEditModal';

type SortField = 'name' | 'table' | 'age' | 'meal';

export const GuestList: React.FC = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [sortBy, setSortBy] = useState<SortField>('name');
  const [filterUnassigned, setFilterUnassigned] = useState(false);
  const [editingName, setEditingName] = useState<string | null>(null);
  const [editValue, setEditValue] = useState('');
  const [editingGuest, setEditingGuest] = useState<Guest | null>(null);

  const guests = useAppStore((s) => s.guests);
  const assignments = useAppStore((s) => s.assignments);
  const tables = useAppStore((s) => s.tables);
  const addGuest = useAppStore((s) => s.addGuest);
  const updateGuest = useAppStore((s) => s.updateGuest);
  const removeGuest = useAppStore((s) => s.removeGuest);
  const removeAssignment = useAppStore((s) => s.removeAssignment);
  const setAssignment = useAppStore((s) => s.setAssignment);
  const lockedGuests = useAppStore((s) => s.lockedGuests);
  const toggleLockGuest = useAppStore((s) => s.toggleLockGuest);

  const filteredAndSorted = useMemo(() => {
    let filtered = guests.filter((guest) => {
      const matchesSearch = guest.name.toLowerCase().includes(searchTerm.toLowerCase());
      const matchesFilter = filterUnassigned ? !assignments[guest.name] : true;
      return matchesSearch && matchesFilter;
    });

    filtered.sort((a, b) => {
      switch (sortBy) {
        case 'name':
          return a.name.localeCompare(b.name);
        case 'table': {
          const tA = assignments[a.name] || 'zzz';
          const tB = assignments[b.name] || 'zzz';
          return tA.localeCompare(tB);
        }
        case 'age':
          return (b.age || 0) - (a.age || 0);
        case 'meal':
          return (a.meal_preference || '').localeCompare(b.meal_preference || '');
        default:
          return 0;
      }
    });

    return filtered;
  }, [guests, searchTerm, sortBy, filterUnassigned, assignments]);

  const handleAddGuest = () => {
    const name = `Guest ${guests.length + 1}`;
    addGuest(createDefaultGuest(name));
  };

  const handleStartEdit = (guest: Guest) => {
    setEditingName(guest.name);
    setEditValue(guest.name);
  };

  const handleSaveEdit = (oldName: string) => {
    const guest = guests.find((g) => g.name === oldName);
    if (guest && editValue.trim() && editValue.trim() !== oldName) {
      updateGuest(oldName, { ...guest, name: editValue.trim() });
    }
    setEditingName(null);
  };

  return (
    <div className="w-full h-full flex flex-col bg-gray-50">
      {/* Header and controls */}
      <div className="p-4 bg-white border-b border-gray-200">
        <h2 className="text-lg font-semibold text-gray-800 mb-3">
          Guests ({guests.length})
        </h2>

        <div className="space-y-3">
          <div className="flex gap-2">
            <input
              type="text"
              placeholder="Search by name..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <button
              onClick={handleAddGuest}
              className="px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 text-sm font-medium"
            >
              Add Guest
            </button>
          </div>

          <div className="flex gap-4 items-center">
            <label className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={filterUnassigned}
                onChange={(e) => setFilterUnassigned(e.target.checked)}
                className="rounded"
              />
              <span>Unassigned only</span>
            </label>

            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as SortField)}
              className="px-3 py-1.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="name">Sort by Name</option>
              <option value="table">Sort by Table</option>
              <option value="age">Sort by Age</option>
              <option value="meal">Sort by Meal</option>
            </select>
          </div>
        </div>
      </div>

      {/* Guest table */}
      <div className="flex-1 overflow-auto">
        <table className="w-full">
          <thead className="bg-gray-100 border-b border-gray-200 sticky top-0">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600">Name</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600">Table</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600">Age</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600">Meal</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600">Groups</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600">Actions</th>
            </tr>
          </thead>
          <tbody>
            {filteredAndSorted.map((guest) => {
              const tableName = assignments[guest.name];
              const isEditing = editingName === guest.name;
              const isLocked = lockedGuests.has(guest.name);

              return (
                <tr
                  key={guest.id}
                  className="border-b border-gray-100 hover:bg-gray-50 transition-colors"
                >
                  {/* Name */}
                  <td className="px-4 py-2.5">
                    {isEditing ? (
                      <input
                        autoFocus
                        value={editValue}
                        onChange={(e) => setEditValue(e.target.value)}
                        onBlur={() => handleSaveEdit(guest.name)}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter') handleSaveEdit(guest.name);
                          if (e.key === 'Escape') setEditingName(null);
                        }}
                        className="w-full px-2 py-1 border border-blue-500 rounded text-sm"
                      />
                    ) : (
                      <span
                        onClick={() => handleStartEdit(guest)}
                        className="cursor-pointer hover:text-blue-600 text-sm"
                      >
                        {guest.name}
                        {isLocked && (
                          <span className="ml-1 text-xs text-orange-500" title="Locked">
                            &#128274;
                          </span>
                        )}
                      </span>
                    )}
                  </td>

                  {/* Table assignment dropdown */}
                  <td className="px-4 py-2.5">
                    <select
                      value={tableName || ''}
                      onChange={(e) => {
                        const val = e.target.value;
                        if (val) {
                          setAssignment(guest.name, val);
                        } else {
                          removeAssignment(guest.name);
                        }
                      }}
                      className="px-2 py-1 border border-gray-300 rounded text-xs focus:outline-none focus:ring-1 focus:ring-blue-500"
                    >
                      <option value="">Unassigned</option>
                      {tables.map((t) => (
                        <option key={t.name} value={t.name}>
                          {t.name}
                        </option>
                      ))}
                    </select>
                  </td>

                  {/* Age */}
                  <td className="px-4 py-2.5 text-sm text-gray-600">
                    {guest.age || '-'}
                  </td>

                  {/* Meal */}
                  <td className="px-4 py-2.5 text-sm text-gray-600">
                    {guest.meal_preference || '-'}
                  </td>

                  {/* Groups */}
                  <td className="px-4 py-2.5 text-xs text-gray-500">
                    {guest.groups.length > 0 ? guest.groups.join(', ') : '-'}
                  </td>

                  {/* Actions */}
                  <td className="px-4 py-2.5">
                    <div className="flex gap-1">
                      <button
                        onClick={() => setEditingGuest(guest)}
                        className="text-xs px-2 py-1 text-blue-600 hover:bg-blue-50 rounded transition-colors"
                      >
                        Edit
                      </button>
                      <button
                        onClick={() => toggleLockGuest(guest.name)}
                        className={`text-xs px-2 py-1 rounded transition-colors ${
                          isLocked
                            ? 'bg-orange-100 text-orange-700 hover:bg-orange-200'
                            : 'text-gray-500 hover:bg-gray-100'
                        }`}
                        title={isLocked ? 'Unlock' : 'Lock to current table'}
                      >
                        {isLocked ? 'Unlock' : 'Lock'}
                      </button>
                      <button
                        onClick={() => removeGuest(guest.name)}
                        className="text-xs px-2 py-1 text-red-600 hover:bg-red-50 rounded transition-colors"
                      >
                        Delete
                      </button>
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>

        {filteredAndSorted.length === 0 && (
          <div className="flex items-center justify-center h-48 text-gray-400 text-sm">
            {guests.length === 0
              ? 'No guests yet. Upload a CSV or add guests manually.'
              : 'No guests match the current filter.'}
          </div>
        )}
      </div>

      {editingGuest && (
        <GuestEditModal
          guest={editingGuest}
          onClose={() => setEditingGuest(null)}
        />
      )}
    </div>
  );
};
