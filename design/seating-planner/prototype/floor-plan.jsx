/* global React */
// Floor plan SVG view: tables laid out on a clean grid with chair markers,
// drag-and-drop guests between tables, hover relationship lines, snap animation.

const { useState, useEffect, useRef, useMemo } = React;

function FloorPlan({
  guests, tables, assignments, setAssignments,
  relIndex, selectedTable, setSelectedTable,
  hoveredGuest, setHoveredGuest,
  showRelLines, viewport, setViewport,
  filterGroup,
}) {
  const W = 1600, H = 1100;
  const cols = 4, rows = 3;
  const cellW = W / cols, cellH = (H - 80) / rows;
  const tableR = 110;
  const chairR = 16;

  const guestById = useMemo(() => {
    const m = {};
    for (const g of guests) m[g.id] = g;
    return m;
  }, [guests]);

  // Position each table at center of its grid cell (with top offset for header)
  const tablePos = useMemo(() => {
    const pos = {};
    tables.forEach((t, i) => {
      const c = i % cols, r = Math.floor(i / cols);
      pos[t.name] = { x: c * cellW + cellW / 2, y: 80 + r * cellH + cellH / 2 };
    });
    return pos;
  }, [tables]);

  // Members per table
  const membersByTable = useMemo(() => {
    const m = {};
    tables.forEach(t => (m[t.name] = []));
    for (const g of guests) if (assignments[g.id] && m[assignments[g.id]]) m[assignments[g.id]].push(g.id);
    return m;
  }, [guests, tables, assignments]);

  // Drag state
  const [drag, setDrag] = useState(null); // { gid, x, y, fromTable }
  const [dropTarget, setDropTarget] = useState(null);
  const svgRef = useRef(null);

  function chairPos(centerX, centerY, idx, total, radius) {
    const angle = (idx / total) * Math.PI * 2 - Math.PI / 2;
    return {
      x: centerX + Math.cos(angle) * radius,
      y: centerY + Math.sin(angle) * radius,
    };
  }

  function svgCoords(evt) {
    const svg = svgRef.current;
    const pt = svg.createSVGPoint();
    pt.x = evt.clientX; pt.y = evt.clientY;
    const ctm = svg.getScreenCTM();
    if (!ctm) return { x: 0, y: 0 };
    const inv = ctm.inverse();
    const local = pt.matrixTransform(inv);
    return { x: local.x, y: local.y };
  }

  function onMouseDown(e, gid, fromTable) {
    e.preventDefault();
    const c = svgCoords(e);
    setDrag({ gid, x: c.x, y: c.y, fromTable });
  }

  useEffect(() => {
    if (!drag) return;
    function move(e) {
      const c = svgCoords(e);
      setDrag(d => d ? { ...d, x: c.x, y: c.y } : d);
      // hit-test tables
      let target = null;
      let bestDist = Infinity;
      for (const t of tables) {
        const p = tablePos[t.name];
        const dx = c.x - p.x, dy = c.y - p.y;
        const d2 = dx * dx + dy * dy;
        if (d2 < (tableR + chairR + 16) ** 2 && d2 < bestDist) {
          bestDist = d2; target = t.name;
        }
      }
      setDropTarget(target);
    }
    function up() {
      if (drag && dropTarget && dropTarget !== drag.fromTable) {
        // capacity check: if over capacity, swap with someone
        const target = dropTarget;
        const targetMembers = membersByTable[target];
        const targetTable = tables.find(t => t.name === target);
        if (targetMembers.length < targetTable.capacity) {
          setAssignments(prev => ({ ...prev, [drag.gid]: target }));
        } else {
          // swap with a random member of target
          const swapId = targetMembers[targetMembers.length - 1];
          setAssignments(prev => ({ ...prev, [drag.gid]: target, [swapId]: drag.fromTable }));
        }
      }
      setDrag(null); setDropTarget(null);
    }
    window.addEventListener("mousemove", move);
    window.addEventListener("mouseup", up);
    return () => {
      window.removeEventListener("mousemove", move);
      window.removeEventListener("mouseup", up);
    };
  }, [drag, dropTarget, tables, tablePos, membersByTable, setAssignments]);

  // Relationship lines for the hovered guest
  const relLines = useMemo(() => {
    if (!hoveredGuest || !showRelLines) return [];
    const lines = [];
    const fromTable = assignments[hoveredGuest];
    if (!fromTable) return lines;
    const fromPos = tablePos[fromTable];
    if (!fromPos) return lines;
    const fromIdx = membersByTable[fromTable].indexOf(hoveredGuest);
    const fromCount = membersByTable[fromTable].length;
    const fromChair = chairPos(fromPos.x, fromPos.y, fromIdx, fromCount, tableR + chairR + 4);
    for (const g of guests) {
      if (g.id === hoveredGuest) continue;
      const r = relIndex.get(hoveredGuest + "|" + g.id);
      if (!r) continue;
      const t = assignments[g.id]; if (!t) continue;
      const tp = tablePos[t]; if (!tp) continue;
      const idx = membersByTable[t].indexOf(g.id);
      const cnt = membersByTable[t].length;
      const ch = chairPos(tp.x, tp.y, idx, cnt, tableR + chairR + 4);
      lines.push({ from: fromChair, to: ch, w: r.w, type: r.type });
    }
    return lines;
  }, [hoveredGuest, showRelLines, assignments, tablePos, guests, membersByTable, relIndex]);

  // Hover tooltip handled by parent
  function onChairEnter(e, gid) { setHoveredGuest(gid); }
  function onChairLeave() { setHoveredGuest(null); }

  return (
    <svg ref={svgRef} className="floorplan" viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="xMidYMid meet">
      <defs>
        <pattern id="paperGrain" width="60" height="60" patternUnits="userSpaceOnUse">
          <rect width="60" height="60" fill="transparent"/>
        </pattern>
      </defs>

      {/* Aisle dashed lines */}
      <line x1={W/2} y1={20} x2={W/2} y2={H-20} stroke="var(--rule-2)" strokeWidth="1" strokeDasharray="3 6"/>
      <line x1={20} y1={H/2} x2={W-20} y2={H/2} stroke="var(--rule-2)" strokeWidth="1" strokeDasharray="3 6"/>

      {/* Compass / N marker */}
      <g transform={`translate(${W-80}, 60)`}>
        <circle r="22" fill="none" stroke="var(--rule)" strokeWidth="1"/>
        <text textAnchor="middle" dy="4" fontFamily="var(--font-mono)" fontSize="10" letterSpacing="2" fill="var(--ink-3)">N</text>
        <line x1="0" y1="-22" x2="0" y2="-30" stroke="var(--ink)" strokeWidth="1"/>
      </g>

      {/* Head table label area */}
      <text x={W/2} y={56} textAnchor="middle" fontFamily="var(--font-display)" fontStyle="italic" fontSize="18" fill="var(--ink-3)" letterSpacing="6">— HEAD OF ROOM —</text>

      {/* Relationship lines (under tables) */}
      {relLines.map((l, i) => (
        <line key={i}
          x1={l.from.x} y1={l.from.y} x2={l.to.x} y2={l.to.y}
          className={`rel-line ${l.w >= 0 ? 'positive' : 'negative'}`}
          strokeWidth={Math.abs(l.w) >= 4 ? 2 : 1.2}
        />
      ))}

      {/* Tables */}
      {tables.map((t, ti) => {
        const pos = tablePos[t.name];
        const members = membersByTable[t.name];
        const seats = t.capacity;
        const isSel = selectedTable === t.name;
        const isDrop = dropTarget === t.name;
        return (
          <g key={t.name}
            className={`fp-table ${isSel ? 'selected' : ''} ${isDrop ? 'drop-target' : ''}`}
            onClick={() => setSelectedTable(isSel ? null : t.name)}>
            {/* Table outer ring */}
            <circle className="fp-ring" cx={pos.x} cy={pos.y} r={tableR}
              fill="var(--paper-2)" stroke={isSel ? 'var(--ink)' : 'var(--walnut)'} strokeWidth={isSel ? 2.4 : 1.4}
              style={{ transition: 'stroke 200ms, stroke-width 200ms' }}/>
            {/* Inner ring decorative */}
            <circle cx={pos.x} cy={pos.y} r={tableR - 16}
              fill="none" stroke="var(--rule)" strokeWidth="0.8" strokeDasharray="2 4"/>
            {/* Table name */}
            <text className="fp-table-label" x={pos.x} y={pos.y - 6} fontSize="26">{t.name}</text>
            <text className="fp-table-cap" x={pos.x} y={pos.y + 18} fontSize="11">
              {`${members.length} / ${t.capacity}`}
            </text>
            {/* Chairs */}
            {Array.from({ length: seats }).map((_, idx) => {
              const c = chairPos(pos.x, pos.y, idx, seats, tableR + chairR + 6);
              const gid = members[idx];
              const g = gid ? guestById[gid] : null;
              const isHover = gid && hoveredGuest === gid;
              const isVip = g && g.vip;
              const conflict = gid ? hasConflict(gid, members, relIndex) : false;
              const isDragging = drag && drag.gid === gid;
              const dim = filterGroup && filterGroup !== 'all' && g && g.groups[0] !== filterGroup;
              const matched = filterGroup && filterGroup !== 'all' && g && g.groups[0] === filterGroup;
              const labelOutside = c.y > pos.y;
              return (
                <g key={idx} transform={`translate(${c.x}, ${c.y})`} style={{ opacity: dim ? 0.18 : 1, transition: 'opacity 200ms' }}>
                  <circle r={chairR}
                    className={`chair ${!gid ? 'empty' : ''} ${isVip ? 'vip' : ''} ${conflict ? 'conflict' : ''}`}
                    style={{
                      opacity: isDragging ? 0.3 : 1,
                      fill: matched ? 'var(--gilt)' : undefined,
                      strokeWidth: matched ? 2 : undefined,
                    }}
                    onMouseEnter={(e) => gid && onChairEnter(e, gid)}
                    onMouseLeave={onChairLeave}
                    onMouseDown={(e) => gid && onMouseDown(e, gid, t.name)}
                  />
                  {gid && !isDragging && (
                    <>
                      <text textAnchor="middle" dy="4"
                        fontFamily="var(--font-mono)" fontSize="9"
                        fontWeight="600" fill="var(--ink)" style={{ pointerEvents: 'none' }}>
                        {WTM.initials(g.name)}
                      </text>
                      <text className="fp-name" y={labelOutside ? chairR + 14 : -chairR - 6} fontSize="12"
                        style={{ fontWeight: isHover ? 600 : 400 }}>
                        {g.first} {g.last[0]}.
                      </text>
                    </>
                  )}
                </g>
              );
            })}
          </g>
        );
      })}

      {/* Dragging ghost */}
      {drag && (() => {
        const g = guestById[drag.gid];
        return (
          <g transform={`translate(${drag.x}, ${drag.y})`} style={{ pointerEvents: "none" }}>
            <circle r={chairR + 2} fill="var(--gilt)" stroke="var(--ink)" strokeWidth="1.5"/>
            <text className="fp-name" y={4} fontSize="9" fill="var(--ink)">{WTM.initials(g.name)}</text>
            <text className="fp-name" y={chairR + 14} fontSize="11">{g.first} {g.last[0]}.</text>
          </g>
        );
      })()}
    </svg>
  );
}

function hasConflict(gid, members, relIndex) {
  for (const m of members) {
    if (m === gid) continue;
    const r = relIndex.get(gid + "|" + m);
    if (r && r.w <= -3) return true;
  }
  return false;
}

window.FloorPlan = FloorPlan;
