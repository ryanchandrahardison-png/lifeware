# Lifeware Development Requirements Tracker

Purpose:
This file captures the current project requirements and guardrails so future changes do not drift or accidentally remove previously requested behavior.

## Source Baseline
- Start from the latest uploaded project ZIP unless explicitly told otherwise.
- Preserve working behavior unless the user explicitly asks to change it.
- Do not redesign architecture unless necessary.
- Build features incrementally.
- Avoid unnecessary complexity.
- Maintain high performance.

## Application Architecture
lifeware/
├── app.py
├── requirements.txt
├── core/
│   ├── state.py
│   ├── calendar_utils.py
│   ├── layout.py
│   └── calendar_event_form.py
└── pages/
    ├── home.py
    ├── calendarList.py
    ├── calendarEvent.py
    ├── actions.py
    ├── delegations.py
    └── routines.py

## Navigation / Left Menu Requirements
- Keep the custom left menu visible.
- Keep the left menu below "Session File".
- Remove the extra/default menu above "Session File".
- Do not remove or alter the manual sidebar navigation unless explicitly requested.
- Preserve these menu items unless explicitly requested otherwise:
  - Home
  - Calendar
  - Actions
  - Delegations
  - Routines

## Calendar View Requirements
- Group calendar entries by day.
- Under each day, list events in a table/grid style layout.
- The Start field should display time only.
- The End field should display time only.
- No checkbox column.
- No per-field buttons.
- True row click selection must remain enabled:
  - clicking anywhere on a row opens the event view for that event.
- Keep the calendar sorted by start time.
- Keep the "Add Event" action.
- Implementation note:
  - true row click selection is implemented with Streamlit selectable tables
  - if Streamlit renders a selection column, hide it so no checkbox column is visible

## Event View Requirements
- Event View is frozen unless explicitly requested.
- Do not change the Event View layout or behavior unless the user specifically asks.
- Current behavior:
  - separate Calendar Event page
  - used for Add and Edit
  - fields: Title, Description, Status, Start Date, Start Time, End Date, End Time
  - Save/Create, Delete, Back behavior already implemented

## Calendar Data Model Requirements
- Keep canonical event payload fields consistent:
  - title
  - description
  - status
  - start_utc
  - end_utc
- Calendar list should read canonical UTC fields.
- Do not mutate events during calendar rendering.

## Current Known Intent
The user wants the app to feel more like Asana over time, but without unnecessary architecture changes.
For now:
- preserve the left menu
- preserve the frozen Event View
- improve the Calendar View carefully and incrementally

## Change Control Instructions
Before making changes:
1. Read this file first.
2. Summarize the requirements you are preserving.
3. State exactly which files you will modify.
4. Do not modify unrelated files.
5. After changes, confirm which prior requirements remain intact.

## Prompting Instruction
When continuing development in a new conversation, the assistant should be told to:
- start with the uploaded ZIP
- read this requirements tracker first
- preserve all requirements in this file unless explicitly overridden
- then apply only the newly requested change
