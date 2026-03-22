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

## Control File Governance
- Canonical active control files are root-level only:
  - `NEXT_AGENT_HANDOFF.md`
  - `execution_state.json`
  - `LIFEWARE_REQUIREMENTS_TRACKER.md`
- Archive stale/superseded execution artifacts in:
  - `specifications/executionState/archive/`
  - `openAI/archive/`
- Future agents must only update canonical root control files for active execution state.

## GUI Freeze
- Current screen designs are intentionally preserved.
- Refactors must avoid changing layouts, flows, labels, or widgets unless fixing a functional defect or with explicit approval.
- Architectural cleanup should happen behind the current screens.
- Frozen functional screens/pages:
  - Home
  - Calendar
  - Actions
  - Delegations
  - Projects
  - Routines
  - My Day

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
- In Calendar View, events before the current date/time must appear under a separate **Past Events** section.
- Keep the "New Event"/add event action available in Calendar View.
- Implementation note:
  - true row click selection is implemented with Streamlit selectable tables
  - if Streamlit renders a selection column, hide it so no checkbox column is visible

## Event View Requirements
- Event View remains the baseline interaction pattern for editable detail screens unless explicitly requested otherwise.
- Keep the Event View layout and behavior available for Add and Edit.
- Current behavior:
  - separate Calendar Event page
  - used for Add and Edit
  - fields: Title, Description, Status, Start Date, Start Time, End Date, End Time
  - Save/Create, Delete, Back behavior already implemented
- "Freeze Calendar/Event" means preserve this editable behavior and avoid unrelated redesigns; it does not mean disable New Event or make Event View read-only unless explicitly requested.
- In Event View, do not allow start date/time before the current date/time.
- In Event View, do not allow end date/time before start date/time.
- In Event View, if the selected end date equals the selected start date, the end time picker must not allow times before the selected start time.
- In Event View, when saving changes to an existing event, do not re-check start/end date-time validation rules.
- In Event View, the end date picker must gray out dates before the selected start date.
- In Event View, if the selected start date is today, the start time picker must not allow times before the current time window.
- In Event View, the start date picker must gray out dates before today.

## Actions View Requirements
- Actions list must support true row click selection:
  - clicking anywhere on a row opens the separate Action Details page for that action.
- Action Details page is editable.
- Action Details page must include:
  - Title
  - Details
  - Due Date (date only)
  - Status
  - Save, Delete, and Back actions styled like Event View actions
- Do not show a Source field in Action Details.
- Due Date must follow the same guardrail pattern as Event View date handling:
  - preserve stored past dates for existing records
  - only apply minimum-date restrictions when creating a new record in the future
- When a new GTD JSON file is loaded, any prior action selection state must be cleared to prevent stale details from a previous file.

## Delegations View Requirements
- Delegations list must support true row click selection:
  - clicking anywhere on a row opens the separate Delegation Details page for that item.
- Delegation Details page is editable.
- Delegation Details page must include Save, Delete, and Back actions styled like Event View actions.
- Do not show a Source field in Delegation Details.
- When a new GTD JSON file is loaded, any prior delegation selection state must be cleared to prevent stale details from a previous file.

## Projects View Requirements
- Project Details page behavior is considered stable unless explicitly changed by the user.
- In Project Details, project-level action buttons must follow this layout:
  - `Back` remains available near the top of the page.
  - `Add Task` and `Add Delegation` remain in the linked-item action area.
  - `Save` and `Delete` must appear below `Add Task` / `Add Delegation`.
- In Project Details, the project-level primary save button label must be `Save` (not `Save Changes`).
- When entering Project Details from Projects list or New Project flow, clear stale project UI/runtime flags so persisted projects keep the same updated layout and modal behavior across re-entry.
- In linked-item modal opened from Project Details:
  - Remove the `Back` button from the editable form controls.
  - Keep `Save` and `Delete` form actions.
  - The save button label must be `Save` (not `Save Changes`).
  - After successful `Save`, the modal must close.
  - After successful `Delete`, the modal must close.

## Calendar Data Model Requirements
- The calendar must always read from the currently loaded GTD JSON in `st.session_state.data`.
- Keep canonical event payload fields consistent:
  - title
  - description
  - status
  - start_utc
  - end_utc
- Calendar list should read canonical UTC fields.
- Do not mutate events during calendar rendering.
- GTD reload detection must use file content, not just filename/size, so updated GTD files are reloaded correctly.
- If selectable tables are used for true row click, hide the selection checkbox column and suppress cell focus styling so no checkbox or red click box is visible.

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

- In Event View, opening an existing past event must display that event's actual stored start/end date and time values, not the last selected UI values.

- `core/calendar_event_form.py` must remain syntactically valid and importable after updates.

- Event forms must always contain visible `st.form_submit_button()` controls.
- Default form values passed into `date_input` must always satisfy its `min_value` constraints.
- Before packaging, compile-check key Python files to catch syntax/import errors.
- On GTD reload, clear all selection/view indexes tied to the previous file (calendar, action, delegation) before continuing.
- In read-only Event View for existing events, do not pass `None` as a `date_input(min_value=...)`; only supply `min_value` when a real date constraint exists, to avoid Streamlit TypeError runtime failures.

## Development Workflow Requirements

### Mandatory Git Commit Message

Every change request processed by the AI must produce a Git commit message.

The commit message must always be included in the response alongside the returned ZIP.

Format:

<type>: <short summary>

Details:
- bullet describing key change
- bullet describing key change
- bullet describing key change

Types allowed:
- feat
- fix
- refactor
- docs
- chore

Examples:

fix: resolve missing Streamlit form submit button

Details:
- Added st.form_submit_button() to form
- Prevented Streamlit runtime error
- Updated tracker to record form requirement


feat: freeze calendar, events, actions, and delegations

Details:
- Converted calendar view to read-only
- Converted event page to read-only
- Implemented list → detail navigation for actions
- Implemented list → detail navigation for delegations
- Updated requirements tracker to enforce frozen behavior
- Action and Delegation detail forms must preserve unknown fields by updating existing records instead of replacing them wholesale.
- Action and Delegation detail forms must remove the visible `source` field from the editable details layout.


## Additional Preserved Intent Notes
- Calendar View is now considered stable and should not be changed again unless the user explicitly requests a Calendar change.
- Event View is now considered stable and should not be changed again unless the user explicitly requests an Event change.
- Actions List must include a "New Action" button placed in the same top action area pattern as Calendar View.
- Actions List must be grouped into:
  - Past Due
  - Upcoming
  - Floating (items without a due date)
- Delegations List must include a "New Delegation" button placed in the same top action area pattern as Calendar View.
- Delegations List must be grouped into:
  - Past Due
  - Upcoming
  - Floating (items without a follow-up date)
- New Action and New Delegation flows must open their existing detail pages in create mode rather than introducing a new page pattern.
- Delegation Details must support a Follow Up Date field using the same minimum-date guardrail pattern as Action Due Date handling.
