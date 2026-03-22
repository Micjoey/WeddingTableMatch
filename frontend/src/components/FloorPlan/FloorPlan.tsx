import React, { useRef, useState, useCallback } from 'react';
import { Stage, Layer, Circle, Rect, Text, Group } from 'react-konva';
import Konva from 'konva';
import { useAppStore } from '../../store';
import { TableShape } from '../../types';

const TABLE_RADIUS = 50;
const GUEST_RADIUS = 9;
const GUEST_ORBIT_RADIUS = 54;

// Dimensions per shape
const SHAPE_DIMS: Record<TableShape, { w: number; h: number }> = {
  round: { w: TABLE_RADIUS * 2, h: TABLE_RADIUS * 2 },
  rect:  { w: 110, h: 80 },
  long:  { w: 180, h: 60 },
};

// Compute hit-test radius for nearest-table detection
function tableHitRadius(shape: TableShape): number {
  const { w, h } = SHAPE_DIMS[shape];
  return Math.max(w, h) / 2 + GUEST_ORBIT_RADIUS + 20;
}

// Distribute guests around a table based on shape
function guestPositions(count: number, shape: TableShape): { x: number; y: number }[] {
  if (count === 0) return [];
  if (shape === 'round') {
    return Array.from({ length: count }, (_, i) => {
      const angle = (i / count) * Math.PI * 2 - Math.PI / 2;
      return { x: Math.cos(angle) * GUEST_ORBIT_RADIUS, y: Math.sin(angle) * GUEST_ORBIT_RADIUS };
    });
  }
  // For rect/long: arrange along top and bottom edges
  const { w } = SHAPE_DIMS[shape];
  const half = Math.ceil(count / 2);
  const bottom = count - half;
  const yTop = -(SHAPE_DIMS[shape].h / 2) - GUEST_RADIUS - 2;
  const yBot =  (SHAPE_DIMS[shape].h / 2) + GUEST_RADIUS + 2;
  const positions: { x: number; y: number }[] = [];
  for (let i = 0; i < half; i++) {
    const x = half === 1 ? 0 : -w / 2 + 20 + ((w - 40) / (half - 1 || 1)) * i;
    positions.push({ x, y: yTop });
  }
  for (let i = 0; i < bottom; i++) {
    const x = bottom === 1 ? 0 : -w / 2 + 20 + ((w - 40) / (bottom - 1 || 1)) * i;
    positions.push({ x, y: yBot });
  }
  return positions;
}
const COLORS = [
  '#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8',
  '#F7DC6F', '#BB8FCE', '#85C1E2', '#F8B88B', '#A9DFBF',
  '#E8A0BF', '#7EC8E3', '#F4D03F', '#A3D9A5', '#D7BDE2',
];

// Generate wedding-style table positions:
// head table centered at top, guest tables in two symmetrical columns with a center aisle
function layoutTables(
  tables: { shape?: string; tags?: string[]; name?: string }[],
  width: number,
  height: number
): { x: number; y: number }[] {
  const pad = 80;

  // Identify head table (long shape, vip tag, or named "Head Table")
  const headIdx = tables.findIndex(
    (t) => t.shape === 'long' || t.tags?.includes('vip') || t.name === 'Head Table'
  );

  const regularIdxs = tables.map((_, i) => i).filter((i) => i !== headIdx);
  const regularCount = regularIdxs.length;

  const positions: { x: number; y: number }[] = tables.map(() => ({ x: 0, y: 0 }));

  // Head table: horizontally centered near top
  if (headIdx >= 0) {
    positions[headIdx] = { x: width / 2, y: pad + 30 };
  }

  // Guest tables: split evenly into left and right columns flanking an aisle
  const topY = headIdx >= 0 ? pad + 110 : pad;
  const usableH = height - topY - pad;
  const leftCount = Math.ceil(regularCount / 2);
  const rightCount = regularCount - leftCount;
  const maxRows = Math.max(leftCount, rightCount);
  const rowStep = maxRows > 1 ? usableH / (maxRows - 1 || 1) : usableH / 2;

  // Column x positions: left quarter and right quarter of stage
  const leftX = width * 0.25;
  const rightX = width * 0.75;

  regularIdxs.forEach((tableIdx, i) => {
    const isLeft = i < leftCount;
    const posInCol = isLeft ? i : i - leftCount;
    const colCount = isLeft ? leftCount : rightCount;
    const offsetY = colCount > 1 ? 0 : usableH / 2; // center single tables vertically
    const x = isLeft ? leftX : rightX;
    const y = topY + offsetY + posInCol * (colCount > 1 ? usableH / (colCount - 1) : 0);
    positions[tableIdx] = { x, y };
  });

  return positions;
}

export const FloorPlan: React.FC = () => {
  const stageRef = useRef<Konva.Stage>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [stageSize, setStageSize] = useState({ width: 900, height: 600 });
  const [tooltip, setTooltip] = useState<{ text: string; x: number; y: number } | null>(null);
  const [showGuests, setShowGuests] = useState(true);

  const tables = useAppStore((s) => s.tables);
  const guests = useAppStore((s) => s.guests);
  const assignments = useAppStore((s) => s.assignments);
  const setAssignment = useAppStore((s) => s.setAssignment);
  const removeAssignment = useAppStore((s) => s.removeAssignment);
  const selectedGuestName = useAppStore((s) => s.selectedGuestName);
  const selectGuest = useAppStore((s) => s.selectGuest);
  const updateTable = useAppStore((s) => s.updateTable);

  // Compute table positions (use stored x/y or auto-layout)
  const positions = layoutTables(tables, stageSize.width, stageSize.height);
  const tablePositions = tables.map((t, i) => ({
    x: t.x ?? positions[i]?.x ?? 100 + i * 180,
    y: t.y ?? positions[i]?.y ?? 200,
  }));

  // Build guest name -> table name lookup for fast access
  const guestNamesByTable = new Map<string, string[]>();
  tables.forEach((t) => guestNamesByTable.set(t.name, []));
  for (const [guestName, tableName] of Object.entries(assignments)) {
    const list = guestNamesByTable.get(tableName);
    if (list) list.push(guestName);
  }

  // Unassigned guests
  const assignedNames = new Set(Object.keys(assignments));
  const unassigned = guests.filter((g) => !assignedNames.has(g.name));

  // Resize observer
  const containerCallback = useCallback((node: HTMLDivElement | null) => {
    if (!node) return;
    (containerRef as React.MutableRefObject<HTMLDivElement>).current = node;
    const obs = new ResizeObserver((entries) => {
      const { width, height } = entries[0].contentRect;
      if (width > 0 && height > 0) {
        setStageSize({ width, height });
      }
    });
    obs.observe(node);
    // Initial size
    setStageSize({ width: node.offsetWidth, height: node.offsetHeight });
  }, []);

  // Find nearest table to a point
  const findNearestTable = (px: number, py: number): string | null => {
    let best: string | null = null;
    let minDist = Infinity;
    tables.forEach((table, idx) => {
      const tx = tablePositions[idx].x;
      const ty = tablePositions[idx].y;
      const dist = Math.sqrt((tx - px) ** 2 + (ty - py) ** 2);
      const hitR = tableHitRadius(table.shape ?? 'round');
      if (dist < hitR && dist < minDist) {
        minDist = dist;
        best = table.name;
      }
    });
    return best;
  };

  const handleGuestDragEnd = (guestName: string, _e: Konva.KonvaEventObject<DragEvent>) => {
    const stage = stageRef.current;
    if (!stage) return;
    const pos = stage.getPointerPosition();
    if (!pos) return;

    const targetTable = findNearestTable(pos.x, pos.y);
    if (targetTable) {
      setAssignment(guestName, targetTable);
    } else {
      // Dropped outside any table: unassign
      removeAssignment(guestName);
    }
  };

  const handleTableDragEnd = (tableName: string, idx: number, evt: Konva.KonvaEventObject<DragEvent>) => {
    const node = evt.target;
    const table = tables[idx];
    updateTable(tableName, { ...table, x: node.x(), y: node.y() });
  };

  const handleTableWheel = (tableName: string, evt: Konva.KonvaEventObject<WheelEvent>) => {
    evt.evt.preventDefault();
    const table = tables.find(t => t.name === tableName);
    if (!table) return;
    const delta = evt.evt.deltaY > 0 ? 15 : -15;
    updateTable(tableName, { ...table, rotation: ((table.rotation ?? 0) + delta + 360) % 360 });
  };

  return (
    <div className="w-full h-full flex flex-col bg-gray-50">
      <div className="px-4 py-3 bg-white border-b border-gray-200 flex items-center justify-between gap-4">
        <div>
          <h2 className="text-base font-semibold text-gray-800">Floor Plan</h2>
          <p className="text-xs text-gray-400 hidden sm:block">Drag guests · Drag tables · Scroll to rotate</p>
        </div>
        <button
          onClick={() => setShowGuests((v) => !v)}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors cursor-pointer shrink-0 ${
            showGuests ? 'bg-blue-50 text-blue-600 hover:bg-blue-100' : 'bg-gray-100 text-gray-500 hover:bg-gray-200'
          }`}
        >
          <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            {showGuests
              ? <><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0" /></>
              : <><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" /></>
            }
          </svg>
          {showGuests ? 'Guests on' : 'Guests off'}
        </button>
      </div>

      <div className="flex-1 relative" ref={containerCallback}>
        <Stage ref={stageRef} width={stageSize.width} height={stageSize.height}>
          <Layer>
            {tables.map((table, idx) => {
              const cx = tablePositions[idx].x;
              const cy = tablePositions[idx].y;
              const color = COLORS[idx % COLORS.length];
              const members = guestNamesByTable.get(table.name) || [];
              const shape = table.shape ?? 'round';
              const { w, h } = SHAPE_DIMS[shape];
              const gPositions = guestPositions(members.length, shape);

              return (
                <Group
                  key={table.name}
                  x={cx}
                  y={cy}
                  rotation={table.rotation ?? 0}
                  draggable
                  onDragEnd={(e) => handleTableDragEnd(table.name, idx, e)}
                  onWheel={(e) => handleTableWheel(table.name, e)}
                >
                  {/* Table shape */}
                  {shape === 'round' ? (
                    <Circle
                      x={0} y={0}
                      radius={TABLE_RADIUS}
                      fill={color} opacity={0.8}
                      stroke="rgba(0,0,0,0.2)" strokeWidth={2}
                    />
                  ) : (
                    <Rect
                      x={-w / 2} y={-h / 2}
                      width={w} height={h}
                      cornerRadius={shape === 'rect' ? 10 : 6}
                      fill={color} opacity={0.8}
                      stroke="rgba(0,0,0,0.2)" strokeWidth={2}
                    />
                  )}

                  {/* Table name */}
                  <Text
                    x={-w / 2 + 4} y={-9}
                    width={w - 8}
                    text={table.name}
                    fontSize={12} fontStyle="bold"
                    fill="white" align="center"
                    listening={false}
                  />
                  {/* Capacity */}
                  <Text
                    x={-w / 2 + 4} y={5}
                    width={w - 8}
                    text={`${members.length}/${table.capacity}`}
                    fontSize={10} fill="rgba(255,255,255,0.85)"
                    align="center" listening={false}
                  />

                  {/* Guest nodes */}
                  {showGuests && members.map((guestName, gIdx) => {
                    const { x: gx, y: gy } = gPositions[gIdx] ?? { x: 0, y: 0 };
                    const isSelected = selectedGuestName === guestName;

                    return (
                      <React.Fragment key={guestName}>
                        <Circle
                          x={gx} y={gy}
                          radius={GUEST_RADIUS}
                          fill={color}
                          stroke={isSelected ? '#1d4ed8' : '#fff'}
                          strokeWidth={isSelected ? 3 : 1.5}
                          opacity={0.92}
                          draggable
                          onDragStart={(e) => { e.cancelBubble = true; }}
                          onDragEnd={(e) => { e.cancelBubble = true; handleGuestDragEnd(guestName, e); }}
                          onClick={(e) => { e.cancelBubble = true; selectGuest(selectedGuestName === guestName ? null : guestName); }}
                          onMouseEnter={(e) => {
                            const stage = e.target.getStage();
                            const pos = stage?.getPointerPosition();
                            if (pos) setTooltip({ text: guestName, x: pos.x, y: pos.y - 25 });
                            e.target.opacity(1);
                          }}
                          onMouseLeave={(e) => { setTooltip(null); e.target.opacity(0.92); }}
                        />
                        <Text
                          x={gx - GUEST_RADIUS} y={gy - 5}
                          width={GUEST_RADIUS * 2}
                          text={guestName.split(' ').map((word) => word[0]).join('').slice(0, 2)}
                          fontSize={7} fill="#fff" align="center"
                          listening={false}
                        />
                      </React.Fragment>
                    );
                  })}
                </Group>
              );
            })}
          </Layer>
        </Stage>

        {/* Tooltip overlay */}
        {tooltip && (
          <div
            className="absolute bg-gray-900 text-white px-2 py-1 rounded text-xs pointer-events-none z-50"
            style={{ left: tooltip.x + 10, top: tooltip.y }}
          >
            {tooltip.text}
          </div>
        )}
      </div>

      {/* Unassigned guests bar */}
      {unassigned.length > 0 && (
        <div className="p-3 bg-yellow-50 border-t border-yellow-200">
          <p className="text-sm font-semibold text-yellow-800 mb-2">
            Unassigned ({unassigned.length})
          </p>
          <div className="flex flex-wrap gap-1.5">
            {unassigned.map((guest) => (
              <span
                key={guest.name}
                onClick={() => selectGuest(guest.name)}
                className={`px-2 py-1 rounded-full text-xs cursor-pointer transition-colors ${
                  selectedGuestName === guest.name
                    ? 'bg-yellow-400 text-yellow-900'
                    : 'bg-yellow-200 text-yellow-800 hover:bg-yellow-300'
                }`}
              >
                {guest.name}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
