# DERIVED_VIEW_RULES.md

Defines how list views group and filter data.

Pages must not redefine these rules independently.

## Floating
Floating means:
- action has no `due_date`
- delegation has no `follow_up_date`
- project has no `due_date`

## Past Due
Past Due = date < today

## Upcoming
Upcoming = date >= today

## Global Visibility Rules

### Actions List
Show:
- actions where `project_id` is null
- actions where `project_id` exists AND `is_active_global = true`

Hide:
- actions where `project_id` exists AND `is_active_global = false`

### Delegations List
Show:
- delegations where `project_id` is null
- delegations where `project_id` exists AND `is_active_global = true`

Hide:
- delegations where `project_id` exists AND `is_active_global = false`

## Project Visibility
Projects list shows:
- Active
- Someday

Completed projects are hidden unless Show Completed is enabled.

## Project Health
Project health is derived dynamically from linked items and is not stored.

Health states:

### Healthy
At least one active linked item exists.

### Blocked
Active linked items exist, but all active linked items are delegations.

### Stalled
The project has incomplete linked items, but zero active linked items.

### Ready to Complete
All linked items are completed.

Health should be displayed as a row-level badge/label for Active projects.
