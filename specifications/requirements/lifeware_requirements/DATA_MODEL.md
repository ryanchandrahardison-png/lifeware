# Lifeware Data Model Specification

## UUID IDs
All entities use UUID-style random IDs.

## Project
```text
{
  id: string (uuid)
  title: string
  description: string
  due_date: date | null
  status: Someday | Active | Completed
  action_ids: [string]
  delegation_ids: [string]
}
```

## Action
```text
{
  id: string (uuid)
  title: string
  details: string
  due_date: date | null
  status: Open | Completed
  project_id: string | null
  is_active_global: boolean
}
```

## Delegation
```text
{
  id: string (uuid)
  title: string
  details: string
  follow_up_date: date | null
  status: Waiting | Completed
  project_id: string | null
  is_active_global: boolean
}
```

## Event
```text
{
  id: string (uuid)
  title: string
  start_time: datetime
  end_time: datetime
  details: string
}
```

## Canonical Root State
```text
st.session_state.data = {
  "events": {event_id: Event},
  "actions": {action_id: Action},
  "delegations": {delegation_id: Delegation},
  "projects": {project_id: Project}
}
```

## Draft Editor State
Draft project state is temporary editor/session state only and is not part of canonical persisted data.

Conceptual draft editor state may include:
```text
draft_project
draft_actions[]
draft_delegations[]
```
