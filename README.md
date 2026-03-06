# Lifeware Control Engine Starter

This starter reorganizes the app into a small structured Streamlit project with dedicated pages.

## Files
- `app.py` — Streamlit entry point and navigation
- `core/state.py` — session-state initialization and GTD upload/download helpers
- `core/calendar_utils.py` — calendar parsing, timezone conversion, and formatting helpers
- `core/layout.py` — shared sidebar/session file UI
- `pages/home.py` — landing page
- `pages/calendarList.py` — calendar list page
- `pages/calendarEvent.py` — add/edit event page
- `pages/actions.py` — actions page
- `pages/delegations.py` — delegations page
- `pages/routines.py` — routines page

## Run locally
```bash
streamlit run app.py
```

## Current scope
- Upload GTD JSON once per session
- Download updated GTD JSON
- Calendar list and calendar event editing are split into separate pages
- Actions / Delegations / Routines are simple list pages for now

## Planned next steps
- Normalize actions, delegations, and routines into detail pages
- Add validation and archived-node handling in the UI layer
- Add service modules and storage abstraction
