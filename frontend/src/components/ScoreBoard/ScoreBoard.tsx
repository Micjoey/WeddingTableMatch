import React, { useEffect } from 'react';
import { useAppStore } from '../../store';
import { TableCard } from '../TableCard/TableCard';

export const ScoreBoard: React.FC = () => {
  const guests = useAppStore((s) => s.guests);
  const tables = useAppStore((s) => s.tables);
  const assignments = useAppStore((s) => s.assignments);
  const tableScores = useAppStore((s) => s.tableScores);
  const selectedTableName = useAppStore((s) => s.selectedTableName);
  const selectTable = useAppStore((s) => s.selectTable);
  const updateScores = useAppStore((s) => s.updateScores);
  const isLoading = useAppStore((s) => s.isLoading);

  // Debounced score update when assignments change
  useEffect(() => {
    if (Object.keys(assignments).length === 0) return;
    const timer = setTimeout(() => {
      updateScores();
    }, 600);
    return () => clearTimeout(timer);
  }, [assignments, updateScores]);

  // Computed stats
  const assignedCount = Object.keys(assignments).length;
  const unassignedCount = guests.length - assignedCount;

  // Average grade: convert grades to numbers, average, convert back
  const gradeMap: Record<string, number> = { A: 4, B: 3, C: 2, D: 1, F: 0 };
  const gradeColor: Record<string, string> = { A: 'text-emerald-600', B: 'text-blue-600', C: 'text-amber-600', D: 'text-orange-600', F: 'text-red-600' };
  const reverseGrade = ['F', 'D', 'C', 'B', 'A'];
  const avgGradeNum =
    tableScores.length > 0
      ? tableScores.reduce((sum, s) => sum + (gradeMap[s.grade] ?? 0), 0) / tableScores.length
      : -1;
  const averageGrade = avgGradeNum >= 0 ? reverseGrade[Math.round(avgGradeNum)] || '—' : '—';

  // Happiness: % of guest-pairs at same table who have positive relationships
  const totalPositivePairs = tableScores.reduce((sum, s) => sum + s.pos_pairs, 0);
  const totalNegativePairs = tableScores.reduce((sum, s) => sum + s.neg_pairs, 0);
  const totalPairs = tableScores.reduce((sum, s) => sum + s.pos_pairs + s.neg_pairs + s.neu_pairs, 0);
  const happinessPct = totalPairs > 0 ? Math.round((totalPositivePairs / totalPairs) * 100) : null;

  // Build score lookup by table name
  const scoreByTable = new Map(tableScores.map((s) => [s.table, s]));

  // Get guest names assigned to each table
  const getTableGuestNames = (tableName: string): string[] => {
    return Object.entries(assignments)
      .filter(([, t]) => t === tableName)
      .map(([guestName]) => guestName)
      .sort();
  };

  return (
    <div className="flex flex-col h-full bg-gray-50">
      {/* Summary Stats */}
      <div className="p-4 bg-white border-b border-gray-200">
        <div className="flex items-baseline justify-between mb-4">
          <h2 className="text-base font-semibold text-gray-800">Summary</h2>
          <span className="text-xs text-gray-400">A = great fit · F = conflict</span>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div className="bg-gray-50 p-3 rounded-lg">
            <p className="text-xs text-gray-500">Guests</p>
            <p className="text-2xl font-bold text-gray-900">{guests.length}</p>
            <p className="text-xs text-gray-400 mt-0.5">{assignedCount} seated</p>
          </div>

          <div className="bg-gray-50 p-3 rounded-lg">
            <p className="text-xs text-gray-500">Tables</p>
            <p className="text-2xl font-bold text-gray-900">{tables.length}</p>
            <p className="text-xs text-gray-400 mt-0.5">{tableScores.length} scored</p>
          </div>

          <div className="bg-gray-50 p-3 rounded-lg">
            <p className="text-xs text-gray-500">Seating Quality</p>
            <p className={`text-2xl font-bold ${averageGrade !== '—' ? gradeColor[averageGrade] : 'text-gray-400'}`}>{averageGrade}</p>
            <p className="text-xs text-gray-400 mt-0.5">avg table grade</p>
          </div>

          <div className="bg-gray-50 p-3 rounded-lg">
            <p className="text-xs text-gray-500">Happy Pairs</p>
            <p className="text-2xl font-bold text-emerald-600">
              {happinessPct !== null ? `${happinessPct}%` : '—'}
            </p>
            <p className="text-xs text-gray-400 mt-0.5">{totalPositivePairs} pos · {totalNegativePairs} neg</p>
          </div>
        </div>

        {unassignedCount > 0 && (
          <div className="mt-3 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
            <p className="text-sm text-yellow-800">
              <span className="font-semibold">{unassignedCount}</span> guests
              still unassigned
            </p>
          </div>
        )}

        {isLoading && (
          <div className="mt-3 p-3 bg-blue-50 border border-blue-200 rounded-lg">
            <p className="text-sm text-blue-800">Updating scores...</p>
          </div>
        )}
      </div>

      {/* Table Cards */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {tables.map((table) => (
          <TableCard
            key={table.name}
            table={table}
            guestNames={getTableGuestNames(table.name)}
            score={scoreByTable.get(table.name)}
            isSelected={selectedTableName === table.name}
            onSelect={selectTable}
          />
        ))}
      </div>
    </div>
  );
};
