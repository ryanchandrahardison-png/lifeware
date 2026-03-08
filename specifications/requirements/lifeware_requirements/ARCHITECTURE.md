# Lifeware Architecture Specification

## Application Scope
Lifeware is a single-user GTD system and life operating system.

## Canonical State
Canonical persisted application state is stored only in `st.session_state.data`.

Developers and architects must treat this as the single source of truth for persisted application data.

## Canonical Top-Level Collections
The canonical data collections are:
- `events`
- `actions`
- `delegations`
- `projects`

Canonical collections are UUID-keyed dictionaries.

## Navigation Pattern
All major entities follow the same UI navigation model:

List → Detail

This applies to:
- Calendar
- Actions
- Delegations
- Projects

## Canonical Detail Pattern
The Event View is the canonical layout for detail pages.

All detail screens must contain, as applicable:
- Title
- Date fields
- Details / Description
- Save
- Delete
- Back

Action, Delegation, and Project detail views must visually match the Event View pattern as closely as practical.

## Data Integrity Principles
- All entities must use UUID-style random identifiers.
- Items must not be duplicated across canonical collections.
- Pages render and request mutations.
- Pages do not own business rules.
- Business rules belong in shared mutation logic and derived-view logic.
- Load-time normalization and integrity repair are accepted safeguards.

## Accepted Internal Architecture Decisions
The following are accepted architecture decisions:
- canonical collections are UUID-keyed dictionaries
- load-time normalization / integrity repair is allowed
- atomic-style save orchestration is acceptable for current phases
- page files must not be the long-term home of business rules
