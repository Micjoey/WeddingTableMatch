/* global React, WTM */
const { useState, useMemo } = React;

function GuestList({ guests, assignments, tables, relIndex, filterGroup, search, onSelect }) {
  const filtered = useMemo(() => {
    return guests.filter(g => {
      if (filterGroup && filterGroup !== "all" && g.groups[0] !== filterGroup) return false;
      if (search) {
        const s = search.toLowerCase();
        if (!g.name.toLowerCase().includes(s) && !g.groupLabel.toLowerCase().includes(s)) return false;
      }
      return true;
    });
  }, [guests, filterGroup, search]);

  const relsFor = (gid) => {
    const list = [];
    for (const g of guests) {
      if (g.id === gid) continue;
      const r = relIndex.get(gid + "|" + g.id);
      if (r && Math.abs(r.w) >= 3) list.push({ name: g.first + " " + g.last[0] + ".", w: r.w, type: r.type });
    }
    return list.slice(0, 3);
  };

  return (
    <div className="guest-grid">
      {filtered.map(g => {
        const t = assignments[g.id];
        const rels = relsFor(g.id);
        return (
          <div key={g.id} className="guest-card" onClick={() => onSelect && onSelect(g.id)}>
            <div className="gc-id mono">{g.id.toUpperCase()}</div>
            <div className="gc-name">
              <span className="first">{g.first}</span>
              {g.last}
            </div>
            <div className="gc-meta">
              <span><b>{g.age}</b></span>
              <span>{g.gender_identity[0]}</span>
              <span>{g.location}</span>
              {g.vip && <span style={{ color: 'var(--gilt-2)' }}>★ VIP</span>}
              {g.accessibility && <span style={{ color: 'var(--walnut-2)' }}>♿ {g.accessibility}</span>}
            </div>
            <div className="group-tag">{g.groupLabel}</div>
            <div className="gc-row">
              <span className="label">Meal</span>
              <span style={{ fontFamily: 'var(--font-display)', fontStyle: 'italic', fontSize: 16 }}>{g.meal_preference}</span>
            </div>
            {g.diet_choices.length > 0 && (
              <div className="gc-row">
                <span className="label">Diet</span>
                <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
                  {g.diet_choices.map(d => <span key={d} className="dietary-tag">{d}</span>)}
                </div>
              </div>
            )}
            {rels.length > 0 && (
              <div className="gc-row" style={{ alignItems: 'flex-start' }}>
                <span className="label">Ties</span>
                <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 2 }}>
                  {rels.map((r, i) => (
                    <div key={i} style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13 }}>
                      <span style={{ fontFamily: 'var(--font-display)', fontStyle: 'italic' }}>{r.name}</span>
                      <span className="mono" style={{ fontSize: 10, color: r.w > 0 ? 'var(--mint)' : 'var(--crimson)' }}>
                        {r.type.toUpperCase()} {r.w > 0 ? '+' : ''}{r.w}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
            <div className="gc-table">
              <span className="eyebrow">Seated at</span>
              <span className="tname">{t || '—'}</span>
            </div>
          </div>
        );
      })}
    </div>
  );
}

function TablesView({ guests, tables, assignments, relIndex }) {
  const guestById = useMemo(() => {
    const m = {}; for (const g of guests) m[g.id] = g; return m;
  }, [guests]);
  return (
    <div className="tables-grid">
      {tables.map(t => {
        const memberIds = guests.filter(g => assignments[g.id] === t.name).map(g => g.id);
        const members = memberIds.map(id => guestById[id]);
        const score = WTM.scoreTable(memberIds, relIndex);
        const ages = members.map(m => m.age);
        const avgAge = ages.length ? Math.round(ages.reduce((a, b) => a + b, 0) / ages.length) : 0;
        const dietCount = members.reduce((acc, m) => acc + (m.diet_choices.length > 0 ? 1 : 0), 0);
        const groups = [...new Set(members.map(m => m.groupLabel))];
        return (
          <div key={t.name} className="table-card">
            <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between' }}>
              <h2>{t.name}</h2>
              <div style={{ textAlign: 'right' }}>
                <div className="display" style={{ fontSize: 36, color: WTM.gradeColor(score.grade), fontWeight: 600, lineHeight: 1 }}>{score.grade}</div>
                <div className="mono" style={{ fontSize: 10, color: 'var(--ink-3)', letterSpacing: '0.14em' }}>
                  {score.mean.toFixed(2)} MEAN
                </div>
              </div>
            </div>
            <div className="tc-meta">
              <span>SEATS {memberIds.length}/{t.capacity}</span>
              <span>·</span>
              <span>{t.tags.join(' · ').toUpperCase()}</span>
            </div>
            <div className="tc-stats">
              <div className="stat"><span className="v">{avgAge}</span><span className="l">Avg Age</span></div>
              <div className="stat"><span className="v">{groups.length}</span><span className="l">Groups</span></div>
              <div className="stat"><span className="v">{dietCount}</span><span className="l">Diet Notes</span></div>
            </div>
            <div className="tc-members">
              {members.map((m, i) => (
                <div key={m.id} className="tc-member">
                  <span className="seat">{String(i + 1).padStart(2, '0')}</span>
                  <span className="who">{m.name} {m.vip && <span style={{ color: 'var(--gilt-2)' }}>★</span>}</span>
                  <span className="meal">{m.meal_preference}</span>
                  <span className="meal" style={{ color: m.diet_choices.length ? 'var(--walnut-2)' : 'transparent' }}>
                    {m.diet_choices[0] || '·'}
                  </span>
                </div>
              ))}
              {Array.from({ length: t.capacity - memberIds.length }).map((_, i) => (
                <div key={'e'+i} className="tc-member" style={{ opacity: 0.4 }}>
                  <span className="seat">{String(memberIds.length + i + 1).padStart(2, '0')}</span>
                  <span className="who" style={{ fontStyle: 'italic', color: 'var(--ink-3)' }}>— empty —</span>
                  <span></span><span></span>
                </div>
              ))}
            </div>
            <div className="mono" style={{ fontSize: 10, color: 'var(--ink-3)', letterSpacing: '0.12em', display: 'flex', justifyContent: 'space-between' }}>
              <span>+{score.pos} HARMONIES</span>
              <span>·{score.neu} NEUTRAL</span>
              <span style={{ color: score.neg ? 'var(--crimson)' : 'var(--ink-3)' }}>−{score.neg} TENSIONS</span>
            </div>
          </div>
        );
      })}
    </div>
  );
}

function PrintSheet({ guests, tables, assignments }) {
  const guestById = useMemo(() => { const m = {}; for (const g of guests) m[g.id] = g; return m; }, [guests]);
  return (
    <div className="print-sheet">
      <div style={{ textAlign: 'center', marginBottom: 24 }}>
        <div className="mono" style={{ fontSize: 10, letterSpacing: '0.4em', color: 'var(--ink-3)' }}>SAVETT · WHITFIELD</div>
      </div>
      <h1>Seating Plan</h1>
      <div className="sub">Saturday · the twelfth of September · two thousand twenty-six</div>
      <div style={{ borderTop: '1px solid var(--gilt)', borderBottom: '1px solid var(--gilt)', padding: '20px 0', marginBottom: 30 }}>
        <div style={{ textAlign: 'center', fontFamily: 'var(--font-display)', fontStyle: 'italic', fontSize: 18, color: 'var(--ink-3)' }}>
          The Hall at Ravenscroft Manor
        </div>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '32px 60px' }}>
        {tables.map(t => {
          const members = guests.filter(g => assignments[g.id] === t.name);
          return (
            <div key={t.name}>
              <div style={{ textAlign: 'center', borderBottom: '1px solid var(--ink)', paddingBottom: 6, marginBottom: 12 }}>
                <div className="mono" style={{ fontSize: 9, letterSpacing: '0.3em', color: 'var(--ink-3)' }}>TABLE</div>
                <div style={{ fontFamily: 'var(--font-display)', fontStyle: 'italic', fontSize: 28 }}>{t.name}</div>
              </div>
              <div style={{ columns: 1 }}>
                {members.map(m => (
                  <div key={m.id} style={{ display: 'flex', justifyContent: 'space-between', padding: '3px 0', fontFamily: 'var(--font-display)', fontSize: 15 }}>
                    <span>{m.name}{m.vip && ' ★'}</span>
                    <span style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--ink-3)', letterSpacing: '0.12em' }}>{m.meal_preference[0]}</span>
                  </div>
                ))}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

window.GuestList = GuestList;
window.TablesView = TablesView;
window.PrintSheet = PrintSheet;
