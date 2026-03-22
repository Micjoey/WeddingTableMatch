import React from 'react';
import { Table, TableScore } from '../../types';

interface TableCardProps {
  table: Table;
  guestNames: string[];
  score?: TableScore;
  isSelected?: boolean;
  onSelect?: (tableName: string) => void;
}

const GRADE_COLORS: Record<string, string> = {
  A: 'text-green-600 bg-green-50',
  B: 'text-blue-600 bg-blue-50',
  C: 'text-yellow-600 bg-yellow-50',
  D: 'text-orange-600 bg-orange-50',
  F: 'text-red-600 bg-red-50',
};

export const TableCard: React.FC<TableCardProps> = ({
  table,
  guestNames,
  score,
  isSelected = false,
  onSelect,
}) => {
  const count = guestNames.length;
  const capacity = table.capacity;
  const percentFull = Math.round((count / capacity) * 100);
  const isFull = count >= capacity;
  const isEmpty = count === 0;
  const grade = score?.grade || 'N/A';
  const gradeColor = GRADE_COLORS[grade] || 'text-gray-600 bg-gray-50';

  return (
    <div
      onClick={() => onSelect?.(table.name)}
      className={`p-4 rounded-lg border-2 transition-all cursor-pointer ${
        isSelected
          ? 'border-blue-500 bg-blue-50 shadow-lg'
          : 'border-gray-200 bg-white hover:border-gray-300 hover:shadow-md'
      }`}
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div>
          <h3 className="font-semibold text-gray-900">{table.name}</h3>
          <p className="text-xs text-gray-500">Capacity: {capacity}</p>
        </div>
        <div className={`text-lg font-bold px-3 py-1 rounded-lg ${gradeColor}`}>
          {grade}
        </div>
      </div>

      {/* Capacity bar */}
      <div className="mb-3">
        <div className="flex justify-between items-center mb-1">
          <span className="text-xs font-medium text-gray-700">
            {count}/{capacity} guests
          </span>
          <span className="text-xs text-gray-500">{percentFull}%</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div
            className={`h-2 rounded-full transition-all ${
              isFull ? 'bg-red-500' : isEmpty ? 'bg-gray-300' : 'bg-green-500'
            }`}
            style={{ width: `${Math.min(percentFull, 100)}%` }}
          />
        </div>
      </div>

      {/* Guest list */}
      <div className="mb-3">
        <p className="text-xs font-semibold text-gray-700 mb-2">Members:</p>
        {guestNames.length === 0 ? (
          <p className="text-xs text-gray-500 italic">No guests assigned</p>
        ) : (
          <div className="space-y-1">
            {guestNames.slice(0, 5).map((name) => (
              <p key={name} className="text-xs text-gray-700 truncate">
                {name}
              </p>
            ))}
            {guestNames.length > 5 && (
              <p className="text-xs text-gray-500 italic">
                +{guestNames.length - 5} more
              </p>
            )}
          </div>
        )}
      </div>

      {/* Score details */}
      {score && (
        <div className="pt-3 border-t border-gray-200 text-xs text-gray-600 space-y-1">
          <p>
            Mean score:{' '}
            <span className="font-semibold text-gray-900">
              {score.mean_score.toFixed(2)}
            </span>
          </p>
          <div className="flex gap-3">
            <span className="text-green-600">+{score.pos_pairs}</span>
            <span className="text-gray-400">{score.neu_pairs} neu</span>
            <span className="text-red-600">-{score.neg_pairs}</span>
          </div>
        </div>
      )}
    </div>
  );
};
