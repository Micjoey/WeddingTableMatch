// Realistic wedding dataset — 120 guests, 12 tables, ~280 relationships
// Loaded as a global `WEDDING_DATA` for the React app.

(function () {
  const FIRST_F = ["Eleanor","Margot","Beatrice","Cecilia","Iris","Rosalind","Vivienne","Hazel","Clementine","Adelaide","Imogen","Saoirse","Maeve","Astrid","Linnea","Genevieve","Ottilie","Cordelia","Juniper","Anneliese","Pearl","Wren","Florence","Marigold","Tabitha","Sigrid","Annika","Phoebe","Romilly","Esme","Greta","Helena","Lucia","Mireille","Noa","Odette","Petra","Saskia","Thea","Verity"];
  const FIRST_M = ["Theodore","Atticus","Silas","Caspian","Felix","August","Rufus","Wendell","Crispin","Barnaby","Casper","Ambrose","Reuben","Elias","Soren","Magnus","Otto","Hugo","Jasper","Lachlan","Cyrus","Edmund","Frederick","Oscar","Percival","Quentin","Reginald","Sebastian","Tobias","Ulysses","Vincent","Walter","Xavier","Yusuf","Zander","Arlo","Beckett","Callum","Dashiell","Emil"];
  const LASTS = ["Whitfield","Ashford","Caldwell","Pemberton","Lockwood","Sinclair","Kingsley","Beaumont","Ravenscroft","Thorne","Marchetti","Halloway","Vance","Quinn","Okafor","Saito","Nakamura","Petrov","Lindgren","Bauer","Morales","Delacroix","Ó Briain","Khoury","Bhatt","Reyes","Castellanos","Dubois","Eriksson","Fontaine","Galanis","Halvorsen","Iqbal","Janssen","Kowalski","Larsen","Mendez","Nilsson","O'Connell","Park"];

  const GROUPS = [
    { key: "bride-family",  label: "Bride's Family",  size: 18 },
    { key: "groom-family",  label: "Groom's Family",  size: 18 },
    { key: "college",       label: "College Friends", size: 16 },
    { key: "work-bride",    label: "Bride's Work",    size: 10 },
    { key: "work-groom",    label: "Groom's Work",    size: 10 },
    { key: "childhood",     label: "Childhood",       size: 12 },
    { key: "neighbors",     label: "Neighbors",       size: 8  },
    { key: "wedding-party", label: "Wedding Party",   size: 10 },
    { key: "family-friends",label: "Family Friends",  size: 12 },
    { key: "plus-ones",     label: "Plus Ones",       size: 6  },
  ];

  const HOBBIES = ["reading","hiking","yoga","cooking","cycling","photography","sailing","tennis","painting","music","travel","gardening","running","skiing","film","theater","wine","golf","pottery","baking"];
  const LANGS = ["English","French","Spanish","German","Italian","Mandarin","Japanese","Portuguese","Arabic","Swedish"];
  const LOCATIONS = ["New York","Brooklyn","Boston","Philadelphia","D.C.","Chicago","San Francisco","Los Angeles","Austin","Seattle","London","Paris","Berlin","Dublin"];
  const DIETS = [
    { key: "none",        label: "—" },
    { key: "vegetarian",  label: "Vegetarian" },
    { key: "vegan",       label: "Vegan" },
    { key: "gluten-free", label: "Gluten-free" },
    { key: "pescatarian", label: "Pescatarian" },
    { key: "kosher",      label: "Kosher" },
    { key: "nut-allergy", label: "Nut allergy" },
    { key: "dairy-free",  label: "Dairy-free" },
  ];
  const MEALS = ["Beef","Chicken","Fish","Vegetarian","Vegan"];
  const RSVP = ["Yes","Yes","Yes","Yes","Yes","Yes","Yes","Yes","Yes","Maybe","Pending"];

  // Seeded RNG so dataset is stable across reloads
  function mulberry32(seed) {
    return function () {
      let t = (seed += 0x6D2B79F5);
      t = Math.imul(t ^ (t >>> 15), t | 1);
      t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }
  const rnd = mulberry32(20260501);
  const pick = (arr) => arr[Math.floor(rnd() * arr.length)];
  const pickN = (arr, n) => {
    const c = arr.slice();
    const out = [];
    for (let i = 0; i < n && c.length; i++) out.push(c.splice(Math.floor(rnd() * c.length), 1)[0]);
    return out;
  };
  const chance = (p) => rnd() < p;

  // ---- Guests
  const guests = [];
  let id = 1;
  for (const g of GROUPS) {
    for (let i = 0; i < g.size; i++) {
      const female = chance(0.52);
      const first = pick(female ? FIRST_F : FIRST_M);
      const last = pick(LASTS);
      const age = g.key === "childhood" ? 28 + Math.floor(rnd() * 12)
        : g.key === "bride-family" || g.key === "groom-family" ? (chance(0.35) ? 55 + Math.floor(rnd() * 25) : 24 + Math.floor(rnd() * 30))
        : g.key === "neighbors" ? 38 + Math.floor(rnd() * 30)
        : 26 + Math.floor(rnd() * 22);
      const single = chance(0.35);
      const meal = pick(MEALS);
      const dietCount = chance(0.55) ? (chance(0.3) ? 2 : 1) : 0;
      const diet = dietCount ? pickN(DIETS.slice(1), dietCount).map(d => d.key) : [];
      guests.push({
        id: `g${String(id).padStart(3, "0")}`,
        name: `${first} ${last}`,
        first, last,
        age,
        gender_identity: female ? "Female" : "Male",
        rsvp: pick(RSVP),
        meal_preference: meal,
        single,
        plus_one: !single && chance(0.3),
        sit_with_partner: !single,
        groups: [g.key],
        groupLabel: g.label,
        hobbies: pickN(HOBBIES, 2 + Math.floor(rnd() * 2)),
        languages: pickN(LANGS, 1 + Math.floor(rnd() * 2)),
        relationship_status: single ? "single" : (chance(0.5) ? "married" : "partnered"),
        location: pick(LOCATIONS),
        diet_choices: diet,
        partner: "",
        vip: g.key === "wedding-party" || (g.key.endsWith("-family") && chance(0.15)),
        accessibility: chance(0.06) ? pick(["mobility","hearing","wheelchair"]) : null,
        notes: "",
      });
      id++;
    }
  }

  // Pair up partners within same group where possible
  for (let i = 0; i < guests.length; i++) {
    const g = guests[i];
    if (g.partner || g.single) continue;
    const candidates = guests.filter(o => !o.partner && !o.single && o.id !== g.id && o.groups[0] === g.groups[0] && o.gender_identity !== g.gender_identity);
    if (candidates.length && chance(0.7)) {
      const p = candidates[Math.floor(rnd() * candidates.length)];
      g.partner = p.id; p.partner = g.id;
      // share a last name sometimes
      if (chance(0.6)) p.last = g.last, p.name = `${p.first} ${g.last}`;
    }
  }

  // ---- Tables (12)
  const tableNames = [
    "Magnolia","Wisteria","Camellia","Hydrangea","Peony","Jasmine",
    "Olive","Cypress","Laurel","Myrtle","Sycamore","Rosemary"
  ];
  const tables = tableNames.map((n, i) => ({
    name: n,
    capacity: 10,
    tags: i < 2 ? ["family","head"] : i < 6 ? ["family"] : ["friends"],
    shape: "round",
  }));

  // ---- Relationships (within & across groups)
  const rels = [];
  const seen = new Set();
  function add(a, b, type, strength, notes = "") {
    if (a === b) return;
    const key = a < b ? `${a}|${b}` : `${b}|${a}`;
    if (seen.has(key)) return;
    seen.add(key);
    rels.push({ guest1_id: a, guest2_id: b, relationship: type, strength, notes });
  }

  // Partner = married
  for (const g of guests) if (g.partner && g.id < g.partner) add(g.id, g.partner, "married", 5, "partners");

  // Within-group friendships
  const byGroup = {};
  for (const g of guests) (byGroup[g.groups[0]] ||= []).push(g);
  for (const list of Object.values(byGroup)) {
    for (let i = 0; i < list.length; i++) {
      for (let j = i + 1; j < list.length; j++) {
        const r = rnd();
        if (r < 0.18) add(list[i].id, list[j].id, "best friend", 5);
        else if (r < 0.55) add(list[i].id, list[j].id, "friend", 3);
        else if (r < 0.78) add(list[i].id, list[j].id, "know", 2);
      }
    }
  }

  // Cross-group: bride-side and groom-side mingling, conflicts
  const conflictPairs = [];
  for (let i = 0; i < 14; i++) {
    const a = guests[Math.floor(rnd() * guests.length)];
    const b = guests[Math.floor(rnd() * guests.length)];
    if (a.id === b.id) continue;
    if (chance(0.4)) { add(a.id, b.id, "avoid", -3, "history"); conflictPairs.push([a.id,b.id]); }
    else { add(a.id, b.id, "conflict", -5, "ex / family rift"); conflictPairs.push([a.id,b.id]); }
  }
  // Some neutral cross links
  for (let i = 0; i < 60; i++) {
    const a = guests[Math.floor(rnd() * guests.length)];
    const b = guests[Math.floor(rnd() * guests.length)];
    if (a.groups[0] !== b.groups[0]) add(a.id, b.id, "know", 2);
  }

  // ---- Initial seating: greedy by group with some imbalance to fix
  const assignments = {};
  const tableMap = {};
  tables.forEach(t => (tableMap[t.name] = []));

  // Wedding party at head tables (Magnolia + Wisteria)
  const head = guests.filter(g => g.groups[0] === "wedding-party");
  head.forEach((g, i) => {
    const t = tables[i % 2].name;
    assignments[g.id] = t;
    tableMap[t].push(g.id);
  });

  // Family at family tables, friends at friend tables (with some chaos)
  const remainingTables = tables.filter(t => !tableMap[t.name].length || tableMap[t.name].length < t.capacity);
  for (const g of guests) {
    if (assignments[g.id]) continue;
    let target;
    if (g.groups[0].endsWith("-family") || g.groups[0] === "family-friends") {
      target = tables.slice(0, 6).find(t => tableMap[t.name].length < t.capacity);
    } else {
      target = tables.slice(6).find(t => tableMap[t.name].length < t.capacity);
    }
    target ||= tables.find(t => tableMap[t.name].length < t.capacity);
    if (!target) continue;
    assignments[g.id] = target.name;
    tableMap[target.name].push(g.id);
  }

  // Force two known conflicts onto same table to demonstrate scoring
  if (conflictPairs.length) {
    const [a, b] = conflictPairs[0];
    const ta = assignments[a];
    if (ta) {
      // move b to ta
      const tb = assignments[b];
      tableMap[tb] = tableMap[tb].filter(x => x !== b);
      // bump someone out of ta to where b was
      const bump = tableMap[ta].find(x => x !== a);
      if (bump && tableMap[ta].length >= 10) {
        tableMap[ta] = tableMap[ta].filter(x => x !== bump);
        tableMap[tb].push(bump);
        assignments[bump] = tb;
      }
      tableMap[ta].push(b);
      assignments[b] = ta;
    }
  }

  window.WEDDING_DATA = {
    guests,
    tables,
    relationships: rels,
    initialAssignments: assignments,
    groups: GROUPS,
    diets: DIETS,
  };
})();
