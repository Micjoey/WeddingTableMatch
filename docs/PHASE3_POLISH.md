# Phase 3: Polish and Planner Features

**Goal:** Production-quality for couples. Multi-event support for planners.
**Timeline:** Weeks 9-14
**Depends on:** Phase 2 complete

---

## Steps

### 3.1 Database and persistence
- [ ] Add PostgreSQL with SQLAlchemy ORM
- [ ] Schema: users, events, guests, tables, relationships, assignments
- [ ] Migrate from in-memory to DB-backed API
- [ ] Auto-save assignments on every change
- [ ] Event versioning (snapshot history)

### 3.2 User accounts and auth
- [ ] Email/password registration and login
- [ ] JWT-based auth for API
- [ ] Protected routes in React
- [ ] Password reset flow
- [ ] OAuth option (Google) for convenience

### 3.3 Multi-event support
- [ ] Event list dashboard (planner home screen)
- [ ] Create/duplicate/archive events
- [ ] Per-event guest lists, tables, relationships, assignments
- [ ] Event metadata: name, date, venue, notes

### 3.4 PDF export: seating chart
- [ ] Generate printable seating chart PDF
- [ ] Layout: one page per table or grid overview
- [ ] Include: table name, guest names, meal preferences
- [ ] Optional: accessibility notes, dietary flags

### 3.5 PDF export: place cards
- [ ] Generate individual place cards (8 per page, perforated layout)
- [ ] Include: guest name, table number
- [ ] Optional: meal icon, custom message

### 3.6 RSVP import
- [ ] Import guest list from CSV (already done)
- [ ] Import from Zola API (if available)
- [ ] Import from The Knot (if available)
- [ ] Manual RSVP status toggle in guest list

### 3.7 Shareable read-only link
- [ ] Generate unique share URL per event
- [ ] Read-only view: floor plan + guest assignments
- [ ] No login required for viewers
- [ ] Optional password protection

### 3.8 Mobile-responsive web UI
- [ ] Responsive layout for tablet (floor plan scales)
- [ ] Mobile layout: stacked panels instead of side-by-side
- [ ] Touch-friendly drag-and-drop (long press to grab)
- [ ] Bottom sheet for guest/table details on mobile

### 3.9 Accessibility
- [ ] Keyboard navigation for floor plan (tab between tables, arrow keys between guests)
- [ ] Screen reader labels for all interactive elements
- [ ] WCAG 2.1 AA color contrast compliance
- [ ] Focus indicators on all interactive elements

---

## Acceptance Criteria
- User can create account, save event, return later and resume
- Planner can manage 5+ events simultaneously
- PDF seating chart renders correctly for 20-table event
- Share link works without login
- Mobile layout usable on iPhone SE (smallest common screen)
- Lighthouse accessibility score > 90
