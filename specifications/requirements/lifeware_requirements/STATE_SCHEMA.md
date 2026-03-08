# STATE_SCHEMA.md

This document defines the canonical structure of `st.session_state.data`.

All application pages must treat this structure as authoritative.
Pages may read from it but must not reshape canonical state directly.

## Root Structure
```text
st.session_state.data = {
  "events": {},
  "actions": {},
  "delegations": {},
  "projects": {}
}
```

Each collection is a dictionary keyed by UUID.

## Default Collection Initialization
If a collection is missing during load, it must be initialized as an empty dictionary.

Examples:
```python
data.setdefault("events", {})
data.setdefault("actions", {})
data.setdefault("delegations", {})
data.setdefault("projects", {})
```

## Draft Editor State
Draft project state is temporary editor/session state only.

It must not be persisted into canonical collections before Save Project succeeds.

Conceptual draft editor state may include:
```text
draft_project
draft_actions[]
draft_delegations[]
```

This draft state is not part of the canonical persisted data model.
