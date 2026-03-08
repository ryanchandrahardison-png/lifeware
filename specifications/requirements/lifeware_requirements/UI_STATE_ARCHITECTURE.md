# UI_STATE_ARCHITECTURE.md

Purpose:
Define the required separation between canonical persisted state and temporary UI/editor state.

--------------------------------------------------
1. CANONICAL STATE
--------------------------------------------------

Canonical persisted application state must remain only in:
st.session_state.data

Canonical collections remain:
- events
- actions
- delegations
- projects

Canonical state must not be moved elsewhere.

--------------------------------------------------
2. UI STATE
--------------------------------------------------

Temporary editor and widget-facing state must live in:
st.session_state.ui

Examples:
- draft_action_title
- draft_action_due_date
- draft_action_details
- draft_delegation_name
- draft_delegation_followup_date
- editor buffers
- temporary selection state

UI/editor state is not canonical persisted data.
UI/editor state must not directly mutate canonical collections until the appropriate save/add/commit action is performed.

--------------------------------------------------
3. CONTROL FLAGS
--------------------------------------------------

Rerun/reset/load control flags should live in:
st.session_state.flags

Examples:
- reset_action_editor
- reset_delegation_editor
- reload_project_editor
- pending_focus_target

--------------------------------------------------
4. STREAMLIT LIFECYCLE RULE
--------------------------------------------------

Agents must not directly write to widget-bound session_state keys after the widget has already been instantiated in the same run.

Forbidden pattern:
- render widget using key X
- later in same run write to st.session_state[X]

Required safe pattern:
1. user action occurs
2. business data mutation occurs
3. reset/load flag is stored in st.session_state.flags
4. rerun occurs
5. before widget rendering on next run, UI state defaults are applied
6. flag is cleared

--------------------------------------------------
5. CURRENT IMPLEMENTATION SCOPE
--------------------------------------------------

Current approved scope for this architecture change:

Option A:
Refactor pages/projectItem.py only.

Do not expand this refactor to other editor pages during this pass.

Future backlog item:
Option B:
Apply the same UI state architecture to:
- pages/actionItem.py
- pages/delegationItem.py
- pages/eventItem.py

--------------------------------------------------
6. NON-NEGOTIABLE PRESERVATIONS
--------------------------------------------------

This architecture update must preserve:
- Calendar behavior
- Event detail/view structure
- canonical persisted state only in st.session_state.data
- UUID-backed canonical collections
- project save validation requiring at least 2 linked items total
- project completion gating
- project deletion prompt behavior
- existing Actions and Delegations list behavior unless strictly required
- directly editable date behavior
- no checkbox-gated date entry

--------------------------------------------------
7. INTENT
--------------------------------------------------

The purpose of this rule is to prevent Streamlit widget lifecycle failures, reduce rerun-state defects, and separate:
- canonical data state
- temporary UI/editor state
- rerun/reset control state


--------------------------------------------------
8. EXECUTION STATUS
--------------------------------------------------

Current status:
- Option A for `pages/projectItem.py` is COMPLETE and FROZEN in the active build stream.

Option A execution rule:
- Do not reopen Option A for another Developer pass unless a new defect is explicitly opened.
- Treat Option A as the canonical approved pattern for future reference.

Option B execution rule:
- Option B must remain backlog only until Option A completes the full pipeline and is confirmed stable.
