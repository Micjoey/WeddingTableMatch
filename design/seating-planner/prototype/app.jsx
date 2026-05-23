/* global React, ReactDOM, WTM, FloorPlan, GuestList, TablesView, PrintSheet,
   TweaksPanel, useTweaks, TweakSection, TweakRadio, TweakToggle, TweakSlider, TweakSelect, WEDDING_DATA */

const { useState, useMemo, useEffect, useRef } = React;

function App() {
  const [tweaks, setTweak] = useTweaks(/*EDITMODE-BEGIN*/{
    "showRelLines": true,
    "showChairLabels": true,
    "density": "comfortable",
    "accent": "gilt",
    "tableShape": "round",
    "showMinimap": true,
    "showVipStars": true
  }/*EDITMODE-END*/);

  const [view, setView] = useState("seating"); // seating | guests | tables | print

  // Esc closes the drawer + native click delegation as a fallback for React 18
  // event-delegation issues observed when the prototype is hosted in an iframe.
  useEffect(() => {
    const onKey = (e) => { if (e.key === 'Escape') setSelectedTable(null); };
    const onMouseDown = (e) => {
      const t = e.target;
      if (!t) return;
      // X close button
      if (t.closest && t.closest('.td-close')) { setSelectedTable(null); return; }
      // Topbar tab buttons
      const tab = t.closest && t.closest('.topbar nav .tab');
      if (tab) {
        const labelText = tab.textContent || '';
        if (labelText.includes('Guest List')) setView('guests');
        else if (labelText.includes('Tables')) setView('tables');
        else if (labelText.includes('Print Preview')) setView('print');
        else if (labelText.includes('Floor Plan')) setView('seating');
      }
    };
    window.addEventListener('keydown', onKey);
    document.addEventListener('mousedown', onMouseDown, true);
    return () => {
      window.removeEventListener('keydown', onKey);
      document.removeEventListener('mousedown', onMouseDown, true);
    };
  }, []);
  const [guests] = useState(WEDDING_DATA.guests);
  const [tables] = useState(WEDDING_DATA.tables);
  const [relationships] = useState(WEDDING_DATA.relationships);
  const [assignments, setAssignments] = useState(WEDDING_DATA.initialAssignments);

  const [selectedTable, setSelectedTable] = useState("Magnolia");
  const [hoveredGuest, setHoveredGuest] = useState(null);
  const [solving, setSolving] = useState(null);
  const [filterGroup, setFilterGroup] = useState("all");
  const [search, setSearch] = useState("");
  const [tooltip, setTooltip] = useState(null);

  const relIndex = useMemo(() => WTM.buildRelIndex(relationships), [relationships]);

  // accent variable override
  useEffect(() => {
    const root = document.documentElement;
    const map = {
      gilt: "#C9A77A", walnut: "#8B6F47", sage: "#7A8A6E", crimson: "#9C3A3A", ink: "#2B2B2B"
    };
    root.style.setProperty("--gilt", map[tweaks.accent] || map.gilt);
  }, [tweaks.accent]);

  // Tooltip follows hovered guest
  useEffect(() => {
    if (!hoveredGuest) { setTooltip(null); return; }
    function onMove(e) {
      setTooltip({ x: e.clientX + 14, y: e.clientY + 14, gid: hoveredGuest });
    }
    window.addEventListener("mousemove", onMove);
    return () => window.removeEventListener("mousemove", onMove);
  }, [hoveredGuest]);

  // ---- Auto-arrange w/ animated steps
  function autoArrange() {
    setSolving({ phase: "Indexing relationships", progress: 0 });
    const gen = WTM.autoSolveSteps(guests, tables, assignments, relIndex, 5);
    let pass = 0;
    const phrases = [
      "Reading the room",
      "Mapping affinities",
      "Resolving conflicts",
      "Balancing tables",
      "Polishing the plan",
      "Finalizing seats",
    ];
    function tick() {
      const r = gen.next();
      if (r.done) {
        setSolving({ phase: "Complete", progress: 1 });
        setTimeout(() => setSolving(null), 700);
        return;
      }
      pass++;
      setSolving({ phase: phrases[Math.min(pass, phrases.length - 1)], progress: Math.min(pass / 5, 0.95) });
      setAssignments(r.value.assignments);
      setTimeout(tick, 520);
    }
    setTimeout(tick, 350);
  }

  // ---- Score everything
  const tableScores = useMemo(() => {
    const out = {};
    for (const t of tables) {
      const members = guests.filter(g => assignments[g.id] === t.name).map(g => g.id);
      out[t.name] = WTM.scoreTable(members, relIndex);
    }
    return out;
  }, [tables, guests, assignments, relIndex]);

  const overall = useMemo(() => {
    const arr = Object.values(tableScores);
    const total = arr.reduce((a, b) => a + b.total, 0);
    const mean = arr.reduce((a, b) => a + b.mean, 0) / arr.length;
    const pos = arr.reduce((a, b) => a + b.pos, 0);
    const neg = arr.reduce((a, b) => a + b.neg, 0);
    let grade = "C";
    if (mean >= 3) grade = "A";
    else if (mean >= 1.8) grade = "B";
    else if (mean >= 0.6) grade = "C";
    else if (mean >= -0.5) grade = "D";
    else grade = "F";
    return { total, mean, pos, neg, grade };
  }, [tableScores]);

  const guestById = useMemo(() => { const m = {}; for (const g of guests) m[g.id] = g; return m; }, [guests]);

  // ---- Group counts for filter
  const groupCounts = useMemo(() => {
    const c = {};
    for (const g of guests) c[g.groups[0]] = (c[g.groups[0]] || 0) + 1;
    return c;
  }, [guests]);

  // ---- Conflict counter
  const totalConflicts = useMemo(() => Object.values(tableScores).reduce((a, b) => a + b.neg, 0), [tableScores]);
  const unseated = guests.filter(g => !assignments[g.id]).length;

  return (
    <div className={`app ${view === 'print' ? 'print-mode' : ''}`}>
      {/* TOP BAR */}
      <header className="topbar">
        <div className="brand">
          <span className="monogram">M <span className="ampersand">&</span> S</span>
          <span className="meta">Savett · Whitfield · 12.IX.MMXXVI</span>
        </div>
        <nav className="tabs">
          {[
            { k: "seating", n: "01", label: "Floor Plan" },
            { k: "guests",  n: "02", label: "Guest List" },
            { k: "tables",  n: "03", label: "Tables" },
            { k: "print",   n: "04", label: "Print Preview" },
          ].map(t => (
            <button key={t.k} className={`tab ${view === t.k ? 'active' : ''}`} onClick={() => setView(t.k)}>
              <span className="num">{t.n}</span>{t.label}
            </button>
          ))}
        </nav>
        <div className="actions">
          <button className="btn primary" onClick={autoArrange} disabled={!!solving}>
            {solving ? 'Arranging…' : 'Auto-Arrange'}
            <span className="kbd">⌘ ⏎</span>
          </button>
        </div>
      </header>

      {/* LEFT PANEL: Solver options + filters */}
      {view !== 'print' && (
      <aside className="panel-left">
        <div className="panel-section">
          <h3>Solver</h3>
          <SolverToggle label="Maximize known faces" defaultOn />
          <SolverToggle label="Group singles together" />
          <SolverToggle label="Match by hobbies" defaultOn />
          <SolverToggle label="Match by language" />
          <SolverToggle label="Match by age band" />
          <SolverToggle label="Honor must-with" defaultOn />
          <SolverToggle label="Honor forced table" defaultOn />
          <SolverToggle label="Equalize table sizes" defaultOn />
        </div>

        <div className="panel-section" style={{ flex: 1, overflow: 'auto', minHeight: 0 }}>
          <h3>Guest Filters</h3>
          <div className="pill-row">
            <button className={`pill ${filterGroup === 'all' ? 'on' : ''}`} onClick={() => setFilterGroup('all')}>
              All <span className="count">{guests.length}</span>
            </button>
            {WEDDING_DATA.groups.map(g => (
              <button key={g.key}
                className={`pill ${filterGroup === g.key ? 'on' : ''}`}
                onClick={() => setFilterGroup(g.key)}>
                {g.label} <span className="count">{groupCounts[g.key] || 0}</span>
              </button>
            ))}
          </div>
        </div>

        <div className="panel-section">
          <h3>Legend</h3>
          <LegendRow color="var(--mint)" label="Compatible (+3 / +5)" />
          <LegendRow color="var(--crimson)" label="Conflict (−3 / −5)" dashed />
          <LegendRow color="var(--gilt)" label="VIP / head table" filled />
          <LegendRow color="var(--paper)" label="Empty seat" dashed border />
        </div>
      </aside>
      )}

      {/* STAGE */}
      <main className="stage">
        {view === 'seating' && (
          <>
            <FloorPlan
              guests={guests} tables={tables} assignments={assignments}
              setAssignments={setAssignments} relIndex={relIndex}
              selectedTable={selectedTable} setSelectedTable={setSelectedTable}
              hoveredGuest={hoveredGuest} setHoveredGuest={setHoveredGuest}
              showRelLines={tweaks.showRelLines}
              filterGroup={filterGroup}
            />
            {/* Search bar overlay */}
            <div style={{
              position: 'absolute', top: 18, left: 24, right: 24,
              display: 'flex', alignItems: 'center', justifyContent: 'space-between', pointerEvents: 'none'
            }}>
              <div style={{ pointerEvents: 'auto' }}>
                <div className="eyebrow">Section II · Reception</div>
                <div className="display" style={{ fontSize: 24, fontStyle: 'italic' }}>
                  Floor Plan
                </div>
              </div>
              <div className="mono" style={{ fontSize: 11, color: 'var(--ink-3)', letterSpacing: '0.18em' }}>
                {Object.keys(assignments).length} / {guests.length} SEATED · {unseated ? `${unseated} unplaced · ` : ''}{totalConflicts} TENSIONS
              </div>
            </div>

            {solving && <SolvingOverlay phase={solving.phase} progress={solving.progress} />}

            {selectedTable && (() => {
              const t = tables.find(x => x.name === selectedTable);
              if (!t) return null;
              const memberIds = guests.filter(g => assignments[g.id] === t.name).map(g => g.id);
              const members = memberIds.map(id => guestById[id]);
              const score = WTM.scoreTable(memberIds, relIndex);
              const ages = members.map(m => m.age);
              const avgAge = ages.length ? Math.round(ages.reduce((a, b) => a + b, 0) / ages.length) : 0;
              const groups = [...new Set(members.map(m => m.groupLabel))];
              const dietCount = members.reduce((a, m) => a + (m.diet_choices.length > 0 ? 1 : 0), 0);
              return (
                <div className="table-drawer">
                  <div className="td-head">
                    <button className="td-close" onMouseDown={(e) => { e.preventDefault(); setSelectedTable(null); }} onClick={() => setSelectedTable(null)} aria-label="Close">×</button>
                    <div className="td-eyebrow">Table · {t.tags.join(' · ')}</div>
                    <div className="td-name">{t.name}</div>
                    <div className="td-grade-row">
                      <div className="td-grade" style={{ color: WTM.gradeColor(score.grade) }}>{score.grade}</div>
                      <div>
                        <div className="mono" style={{ fontSize: 11, letterSpacing: '0.16em', color: 'var(--ink-3)' }}>MEAN {score.mean.toFixed(2)}</div>
                        <div style={{ display: 'flex', gap: 10, marginTop: 4 }}>
                          <span className="mono" style={{ fontSize: 10, color: 'var(--mint)' }}>+{score.pos}</span>
                          <span className="mono" style={{ fontSize: 10, color: 'var(--ink-3)' }}>·{score.neu}</span>
                          <span className="mono" style={{ fontSize: 10, color: score.neg ? 'var(--crimson)' : 'var(--ink-3)' }}>−{score.neg}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                  <div className="td-stats">
                    <div className="td-stat"><div className="v">{memberIds.length}/{t.capacity}</div><span className="l">Seated</span></div>
                    <div className="td-stat"><div className="v">{avgAge}</div><span className="l">Avg Age</span></div>
                    <div className="td-stat"><div className="v">{groups.length}</div><span className="l">Groups</span></div>
                  </div>
                  <div className="td-members">
                    {members.map((m, i) => (
                      <div key={m.id} className="td-member"
                        onMouseEnter={() => setHoveredGuest(m.id)}
                        onMouseLeave={() => setHoveredGuest(null)}>
                        <span className="seat">{String(i + 1).padStart(2, '0')}</span>
                        <span className="who">
                          {m.name}{m.vip && <span style={{ color: 'var(--gilt-2)' }}> ★</span>}
                          <span className="group">{m.groupLabel}{m.diet_choices.length ? ' · ' + m.diet_choices[0] : ''}</span>
                        </span>
                        <span className="meal">{m.meal_preference}</span>
                      </div>
                    ))}
                    {Array.from({ length: t.capacity - memberIds.length }).map((_, i) => (
                      <div key={'e'+i} className="td-member empty">
                        <span className="seat">{String(memberIds.length + i + 1).padStart(2, '0')}</span>
                        <span className="who">— empty —</span>
                        <span></span>
                      </div>
                    ))}
                  </div>
                  <div className="td-foot">
                    <button className="btn ghost" style={{ flex: 1 }}>Lock Table</button>
                    <button className="btn ghost" style={{ flex: 1 }}>Suggest Swaps</button>
                  </div>
                </div>
              );
            })()}
          </>
        )}
        {view === 'guests' && (
          <div style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
            <div style={{ padding: '24px 28px 0', borderBottom: '1px solid var(--rule-2)' }}>
              <div className="eyebrow">Section I</div>
              <div className="display" style={{ fontSize: 36, fontStyle: 'italic', marginBottom: 8 }}>The Guest List</div>
              <input className="input" placeholder="Search guests, groups, locations…"
                value={search} onChange={e => setSearch(e.target.value)} />
              <div style={{ marginBottom: 14 }}>
                <div className="pill-row">
                  <button className={`pill ${filterGroup === 'all' ? 'on' : ''}`} onClick={() => setFilterGroup('all')}>
                    All <span className="count">{guests.length}</span>
                  </button>
                  {WEDDING_DATA.groups.map(g => (
                    <button key={g.key}
                      className={`pill ${filterGroup === g.key ? 'on' : ''}`}
                      onClick={() => setFilterGroup(g.key)}>
                      {g.label} <span className="count">{groupCounts[g.key] || 0}</span>
                    </button>
                  ))}
                </div>
              </div>
            </div>
            <div style={{ flex: 1, overflow: 'auto' }}>
              <GuestList guests={guests} assignments={assignments} tables={tables}
                relIndex={relIndex} filterGroup={filterGroup} search={search} />
            </div>
          </div>
        )}
        {view === 'tables' && (
          <div style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
            <div style={{ padding: '24px 28px 8px', borderBottom: '1px solid var(--rule-2)' }}>
              <div className="eyebrow">Section III</div>
              <div className="display" style={{ fontSize: 36, fontStyle: 'italic' }}>The Tables</div>
            </div>
            <div style={{ flex: 1, overflow: 'auto' }}>
              <TablesView guests={guests} tables={tables} assignments={assignments} relIndex={relIndex} />
            </div>
          </div>
        )}
        {view === 'print' && (
          <PrintSheet guests={guests} tables={tables} assignments={assignments} />
        )}
      </main>

      {/* RIGHT PANEL: Score board + minimap + selected table */}
      {view !== 'print' && (
      <aside className="panel-right">
        <div className="panel-section">
          <h3>Overall</h3>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: 18, justifyContent: 'space-between' }}>
            <div>
              <div className="display" style={{ fontSize: 64, lineHeight: 1, color: WTM.gradeColor(overall.grade), fontWeight: 600 }}>
                {overall.grade}
              </div>
              <div className="mono" style={{ fontSize: 10, color: 'var(--ink-3)', letterSpacing: '0.18em' }}>
                MEAN {overall.mean.toFixed(2)}
              </div>
            </div>
            <div style={{ textAlign: 'right' }}>
              <div className="display" style={{ fontSize: 22, fontStyle: 'italic' }}>
                {overall.total > 0 ? '+' : ''}{overall.total}
              </div>
              <div className="mono" style={{ fontSize: 10, color: 'var(--ink-3)', letterSpacing: '0.16em' }}>TOTAL POINTS</div>
              <div style={{ display: 'flex', gap: 8, marginTop: 8 }}>
                <span className="mono" style={{ fontSize: 10, color: 'var(--mint)' }}>+{overall.pos}</span>
                <span className="mono" style={{ fontSize: 10, color: 'var(--crimson)' }}>−{overall.neg}</span>
              </div>
            </div>
          </div>
        </div>

        {tweaks.showMinimap && view === 'seating' && (
          <div className="panel-section">
            <h3>Mini Map</h3>
            <Minimap tables={tables} tableScores={tableScores} selectedTable={selectedTable}
              setSelectedTable={setSelectedTable} />
          </div>
        )}

        <div className="panel-section" style={{ flex: 1, overflow: 'auto', minHeight: 0 }}>
          <h3>Tables</h3>
          {tables.map(t => {
            const s = tableScores[t.name];
            const sel = selectedTable === t.name;
            return (
              <div key={t.name} className={`score-row ${sel ? 'selected' : ''}`} onClick={() => setSelectedTable(t.name)}>
                <div className="grade" style={{ color: WTM.gradeColor(s.grade) }}>{s.grade}</div>
                <div>
                  <div className="name">{t.name}</div>
                  <div className="num">
                    {s.pos > 0 && <span style={{ color: 'var(--mint)' }}>+{s.pos} </span>}
                    {s.neg > 0 && <span style={{ color: 'var(--crimson)' }}>−{s.neg} </span>}
                    {s.neu} neu · {s.mean.toFixed(2)}
                  </div>
                </div>
                <div className="num">{guests.filter(g => assignments[g.id] === t.name).length}/{t.capacity}</div>
                <div className="face" style={{ color: WTM.gradeColor(s.grade) }}>{WTM.gradeFace(s.grade)}</div>
              </div>
            );
          })}
        </div>
      </aside>
      )}

      {/* Tooltip */}
      {tooltip && hoveredGuest && (() => {
        const g = guestById[hoveredGuest];
        if (!g) return null;
        const t = assignments[g.id];
        return (
          <div className="tooltip" style={{ left: tooltip.x, top: tooltip.y }}>
            <div className="t-name">{g.name}</div>
            <div className="t-row"><b>{g.groupLabel}</b> · {g.age} · {g.location}</div>
            <div className="t-row">{g.meal_preference}{g.diet_choices.length ? ' · ' + g.diet_choices.join(', ') : ''}</div>
            <div className="t-rels">Seated at {t}</div>
          </div>
        );
      })()}

      {/* Tweaks panel */}
      <TweaksPanel title="Tweaks">
        <TweakSection title="Floor Plan">
          <TweakToggle label="Relationship lines on hover" value={tweaks.showRelLines}
            onChange={v => setTweak('showRelLines', v)} />
          <TweakToggle label="Mini map" value={tweaks.showMinimap}
            onChange={v => setTweak('showMinimap', v)} />
          <TweakToggle label="VIP star markers" value={tweaks.showVipStars}
            onChange={v => setTweak('showVipStars', v)} />
        </TweakSection>
        <TweakSection title="Style">
          <TweakRadio label="Accent" value={tweaks.accent}
            onChange={v => setTweak('accent', v)}
            options={[
              { value: 'gilt', label: 'Gilt' },
              { value: 'walnut', label: 'Walnut' },
              { value: 'sage', label: 'Sage' },
              { value: 'crimson', label: 'Crimson' },
            ]} />
          <TweakSelect label="Density" value={tweaks.density}
            onChange={v => setTweak('density', v)}
            options={[
              { value: 'compact', label: 'Compact' },
              { value: 'comfortable', label: 'Comfortable' },
              { value: 'spacious', label: 'Spacious' },
            ]} />
        </TweakSection>
      </TweaksPanel>
    </div>
  );
}

function SolverToggle({ label, defaultOn }) {
  const [on, setOn] = useState(!!defaultOn);
  return (
    <div className="toggle-row" onClick={() => setOn(v => !v)}>
      <label>{label}</label>
      <div className={`switch ${on ? 'on' : ''}`}></div>
    </div>
  );
}

function LegendRow({ color, label, dashed, filled, border }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '5px 0', fontSize: 13, color: 'var(--ink-2)' }}>
      <span style={{
        width: 22, height: 0,
        borderTop: `${dashed ? '1px dashed' : '2px solid'} ${color}`,
        display: 'inline-block',
      }}></span>
      {label}
    </div>
  );
}

function Minimap({ tables, tableScores, selectedTable, setSelectedTable }) {
  const W = 220, H = 158;
  const cols = 4, rows = 3;
  const cellW = W / cols, cellH = H / rows;
  return (
    <svg viewBox={`0 0 ${W} ${H}`} style={{ width: '100%', height: 'auto', border: '1px solid var(--rule)', background: 'var(--paper-2)' }}>
      <line x1={W/2} y1={0} x2={W/2} y2={H} stroke="var(--rule)" strokeDasharray="2 3"/>
      <line x1={0} y1={H/2} x2={W} y2={H/2} stroke="var(--rule)" strokeDasharray="2 3"/>
      {tables.map((t, i) => {
        const c = i % cols, r = Math.floor(i / cols);
        const cx = c * cellW + cellW / 2, cy = r * cellH + cellH / 2;
        const s = tableScores[t.name];
        const sel = selectedTable === t.name;
        return (
          <g key={t.name} onClick={() => setSelectedTable(t.name)} style={{ cursor: 'pointer' }}>
            <circle cx={cx} cy={cy} r={11}
              fill={WTM.gradeColor(s.grade)} fillOpacity="0.55"
              stroke={sel ? 'var(--ink)' : 'var(--walnut)'} strokeWidth={sel ? 2 : 0.8}/>
            <text x={cx} y={cy + 3} textAnchor="middle" fontSize="9"
              fontFamily="var(--font-display)" fill="var(--ink)" fontWeight="600">{s.grade}</text>
          </g>
        );
      })}
    </svg>
  );
}

function SolvingOverlay({ phase, progress }) {
  return (
    <div className="solving-overlay">
      <div className="ring"></div>
      <div className="label">{phase}…</div>
      <div className="step">PASS · {Math.round(progress * 100)}%</div>
      <div style={{ width: 200, height: 1, background: 'var(--rule)', position: 'relative' }}>
        <div style={{ position: 'absolute', left: 0, top: 0, height: 1, background: 'var(--ink)', width: `${progress * 100}%`, transition: 'width 200ms' }}></div>
      </div>
    </div>
  );
}

ReactDOM.createRoot(document.getElementById('root')).render(<App />);
