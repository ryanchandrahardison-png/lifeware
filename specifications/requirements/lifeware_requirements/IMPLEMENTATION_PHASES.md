# IMPLEMENTATION_PHASES.md

Defines the incremental development order for Lifeware features.

Developers must implement only the currently active phase unless explicitly instructed otherwise.

## CURRENT PHASE
PHASE 1 — Projects MVP Foundation

## Phase 1 Scope
Implement:
- Projects navigation link
- Projects list page
- New Project button
- Project detail page
- Draft project editor
- Draft action creation inside project editor
- Draft delegation creation inside project editor
- Save validation requiring at least 2 linked items total
- Save flow that persists project and linked items together
- Project completion gating
- Project deletion prompt behavior
- Reference integrity safeguards required for this phase

## Phase 1 Project List Behavior
Projects are grouped by:
- Active
- Someday

Completed projects hidden by default, with Show Completed toggle.

Within Active:
- Past Due
- Upcoming
- Floating

## Later Phases
Phase 2 — Actions
Phase 3 — Delegations
Phase 4 — Calendar
Phase 5 — Health Indicators
Phase 6 — Automation

## Explicit Non-Goals
Do NOT implement in Phase 1 unless explicitly requested:
- Stalled for 14 days
- Automatic Next Action Suggestion
- project analytics / intelligence features beyond current derived health labels
- alternate project grouping that replaces status-first grouping
- mutation ledger
- routines / cadenced checklist engine
- routine reset / postpone workflow
