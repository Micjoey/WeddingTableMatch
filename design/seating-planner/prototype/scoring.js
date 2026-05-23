// Scoring + helpers used across the app.
// Lives on window so all <script type="text/babel"> files share it.
window.WTM = (function () {
  function relWeight(rel) {
    const map = { "best friend": 5, "married": 5, "friend": 3, "know": 2, "neutral": 0, "avoid": -3, "conflict": -5 };
    return map[rel] ?? rel.strength ?? 0;
  }

  function buildRelIndex(relationships) {
    const idx = new Map();
    for (const r of relationships) {
      const a = r.guest1_id, b = r.guest2_id;
      const w = (typeof r.strength === "number" ? r.strength : relWeight(r.relationship));
      const ka = a + "|" + b, kb = b + "|" + a;
      idx.set(ka, { w, type: r.relationship, notes: r.notes || "" });
      idx.set(kb, { w, type: r.relationship, notes: r.notes || "" });
    }
    return idx;
  }

  // Score one table given member ids
  function scoreTable(memberIds, relIndex) {
    let total = 0, pos = 0, neg = 0, neu = 0, pairs = 0;
    for (let i = 0; i < memberIds.length; i++) {
      for (let j = i + 1; j < memberIds.length; j++) {
        pairs++;
        const r = relIndex.get(memberIds[i] + "|" + memberIds[j]);
        const w = r ? r.w : 0;
        total += w;
        if (w > 0) pos++;
        else if (w < 0) neg++;
        else neu++;
      }
    }
    const mean = pairs ? total / pairs : 0;
    let grade = "C";
    if (mean >= 3) grade = "A";
    else if (mean >= 1.8) grade = "B";
    else if (mean >= 0.6) grade = "C";
    else if (mean >= -0.5) grade = "D";
    else grade = "F";
    return { total, mean, pos, neg, neu, pairs, grade };
  }

  function gradeColor(grade) {
    return ({ A: "var(--grade-a)", B: "var(--grade-b)", C: "var(--grade-c)", D: "var(--grade-d)", F: "var(--grade-f)" })[grade];
  }

  function gradeFace(grade) {
    return ({ A: "◠", B: "◠", C: "—", D: "︵", F: "✕" })[grade];
  }

  function initials(name) {
    return name.split(/\s+/).map(s => s[0]).slice(0, 2).join("").toUpperCase();
  }

  // Auto-solve: simple greedy with hill climbing on relationship score
  function autoSolve(guests, tables, assignments, relIndex) {
    const a = { ...assignments };
    const memberIds = {};
    for (const t of tables) memberIds[t.name] = [];
    for (const g of guests) {
      const t = a[g.id];
      if (t && memberIds[t]) memberIds[t].push(g.id);
    }

    function tableTotal(name) {
      return scoreTable(memberIds[name], relIndex).total;
    }

    // Multiple swap passes
    for (let pass = 0; pass < 8; pass++) {
      let improved = false;
      for (let i = 0; i < guests.length; i++) {
        for (let j = i + 1; j < guests.length; j++) {
          const ga = guests[i], gb = guests[j];
          const ta = a[ga.id], tb = a[gb.id];
          if (!ta || !tb || ta === tb) continue;
          const before = tableTotal(ta) + tableTotal(tb);
          // perform swap
          memberIds[ta] = memberIds[ta].map(x => x === ga.id ? gb.id : x);
          memberIds[tb] = memberIds[tb].map(x => x === gb.id ? ga.id : x);
          a[ga.id] = tb; a[gb.id] = ta;
          const after = tableTotal(ta) + tableTotal(tb);
          if (after > before + 0.01) { improved = true; }
          else {
            // revert
            memberIds[ta] = memberIds[ta].map(x => x === gb.id ? ga.id : x);
            memberIds[tb] = memberIds[tb].map(x => x === ga.id ? gb.id : x);
            a[ga.id] = ta; a[gb.id] = tb;
          }
        }
      }
      if (!improved) break;
    }
    return a;
  }

  // Generator version: yields after each pass for animation
  function* autoSolveSteps(guests, tables, assignments, relIndex, maxPasses = 6) {
    const a = { ...assignments };
    const memberIds = {};
    for (const t of tables) memberIds[t.name] = [];
    for (const g of guests) {
      const t = a[g.id];
      if (t && memberIds[t]) memberIds[t].push(g.id);
    }
    function tableTotal(name) { return scoreTable(memberIds[name], relIndex).total; }
    for (let pass = 0; pass < maxPasses; pass++) {
      let improved = 0;
      for (let i = 0; i < guests.length; i++) {
        for (let j = i + 1; j < guests.length; j++) {
          const ga = guests[i], gb = guests[j];
          const ta = a[ga.id], tb = a[gb.id];
          if (!ta || !tb || ta === tb) continue;
          const before = tableTotal(ta) + tableTotal(tb);
          memberIds[ta] = memberIds[ta].map(x => x === ga.id ? gb.id : x);
          memberIds[tb] = memberIds[tb].map(x => x === gb.id ? ga.id : x);
          a[ga.id] = tb; a[gb.id] = ta;
          const after = tableTotal(ta) + tableTotal(tb);
          if (after > before + 0.01) improved++;
          else {
            memberIds[ta] = memberIds[ta].map(x => x === gb.id ? ga.id : x);
            memberIds[tb] = memberIds[tb].map(x => x === ga.id ? gb.id : x);
            a[ga.id] = ta; a[gb.id] = tb;
          }
        }
      }
      yield { pass: pass + 1, improved, assignments: { ...a } };
      if (!improved) break;
    }
  }

  return { relWeight, buildRelIndex, scoreTable, gradeColor, gradeFace, initials, autoSolve, autoSolveSteps };
})();
