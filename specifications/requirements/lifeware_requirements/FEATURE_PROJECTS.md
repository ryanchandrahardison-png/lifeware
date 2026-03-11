# Projects Feature Specification

## GTD Definition of a Project
A Project is any desired outcome requiring two or more linked items.

Linked items include:
- Actions
- Delegations

A Project may be saved only when the combined count of linked actions and linked delegations is two or greater.

Examples that qualify:
- 2 actions
- 2 delegations
- 1 action + 1 delegation

Examples that do not qualify:
- 0 linked items
- 1 linked item

## Project Status Values
- Someday
- Active
- Completed

## Projects List
Projects are grouped as:
- Active
- Someday

Completed projects are hidden by default.

A Show Completed toggle allows viewing Completed projects.

## Active Project Grouping
Within Active, projects are grouped into:
- Past Due
- Upcoming
- Floating

Floating = no due date.

Project health is shown as a row-level badge/label and does not replace the above grouping.

## Project Detail
Fields:
- Title
- Due Date
- Description
- Status

Actions:
- Save
- Delete
- Back

## Date Entry Behavior
When the user sets a Project due date, Action due date, or Delegation follow-up date, the corresponding date field must be directly and interactively editable in the UI.

This applies to:
- draft project creation
- saved project editing
- draft action creation
- draft delegation creation
- adding actions to saved projects
- adding delegations to saved projects

The UI must not require a separate checkbox to enable date entry for these fields.

## Draft Project Requirement
Draft project state is a temporary UI/editor construct only.

A draft project must not be persisted into the canonical `projects` collection until it satisfies the GTD minimum of two linked items.

The canonical Project schema must not include `is_draft` or draft-specific status values.

## Draft Task Requirement
Actions and delegations created while building a project draft remain temporary editor state until the user clicks Save Project.

They must not be created in canonical `actions` / `delegations` collections before Save Project succeeds.

## Save Project Behavior
When the user clicks Save Project:
1. Validate that draft linked-item count is at least 2
2. Generate a project UUID
3. Persist the project in `projects`
4. Persist linked actions/delegations in canonical collections
5. Populate `action_ids` / `delegation_ids`
6. Set `project_id` on all linked items

If validation fails, save must be blocked.

If the user cancels, all draft project/task state is discarded.

## Project Completion Gating
A project cannot be marked Completed unless all linked actions and delegations are already Completed.

The Complete Project control must be disabled or unavailable while incomplete linked items exist.

Mutation logic must also reject any attempt to set `project.status = Completed` while any linked item remains incomplete.

## Project Deletion Prompt
If a project contains linked items, the system must prompt the user with these choices:
1. Convert linked items to standalone items
2. Delete linked items with the project
3. Cancel deletion

## Next Actions Within a Project
Project next actions are defined as linked tasks where `is_active_global = true`.

The Project Detail screen must display:
- Next Actions
- Backlog Tasks

Next Actions must appear above Backlog Tasks.

## Project Detail Linked Items Layout (Selected Scope)
For Project Detail in `pages/projectItem.py`:
- The linked-item table and Add Task / Add Delegation controls appear above Save/Delete/Back controls.
- The linked-item table includes all linked actions and delegations.
- Required table columns:
  - Task Name
  - Type
  - Date
- Date source:
  - Action rows use due date
  - Delegation rows use follow-up date
- Group rows as:
  - Completed
  - Past Due
  - Upcoming
  - Floating
- Within non-completed date-based groups, sort by date ascending.
- Row click opens a linked-item modal editor (Action or Delegation variant by entity type).
- Add Task and Add Delegation entry must use modal UI.
- On narrow screens, switch from table to stacked row presentation.
- Save/Delete/Back controls should match Actions/Delegations detail button treatment.

## Business Rule Placement
Project validation and mutation rules are business logic and must not live primarily inside `pages/projectItem.py`.

Required separation:
- `pages/projectItem.py` handles UI orchestration, user input collection, and rendering validation messages
- a project state/service layer outside the page owns save validation, completion gating enforcement, deletion cleanup behavior, and canonical mutation orchestration

The page may call the state/service layer, but it must not become the long-term home of project business rules.

## Project Linked-Item Modal Requirements
For Project Detail linked-item modal behavior:
- The modal must render entity-specific fields matching the linked object type.
  - Action modal required fields: Title, Due Date, Details, Status.
  - Delegation modal required fields: Title, Follow Up Date, Details, Status.
- Field-level behavior parity is required with full-page object editors.
  - If a field is editable on `pages/actionItem.py` / `pages/delegationItem.py`, it must be editable in the corresponding project-linked modal.
  - The same required-field checks, value-shape checks, and status/date handling rules must apply in both modal and full-page editors.
- Constraint ownership must remain outside `pages/projectItem.py`.
  - `pages/projectItem.py` may orchestrate modal UI, but must not become the primary home of Action/Delegation constraint logic.
  - Shared mutation/service helpers remain the canonical enforcement layer so constraints stay consistent across all entry points.
- Save/Delete operations from the modal must call shared Action/Delegation mutation helpers (not page-local business-rule mutations).
- Deletion from the modal must preserve project save-rule protections and referential integrity checks.

### Constraint Consistency Requirement
Constraint behavior for Actions and Delegations must be system-consistent:
- inside Project Detail modal editing
- inside full-page Action/Delegation editing
- outside Project Detail flows generally

Any future constraint change must be implemented once in shared helpers and observed identically by both modal and full-page editors.


### Developer Implementation Contract (Modal Compliance Fix)
To remove ambiguity for the Developer pass, implementation must satisfy all of the following:
1. Modal field parity
   - Action modal renders editable: Title, Due Date, Details, Status.
   - Delegation modal renders editable: Title, Follow Up Date, Details, Status.
2. Shared-constraint parity
   - Modal Save uses the same helper path used by object detail pages for validation/sanitization/persistence.
   - Modal Delete uses the same guarded delete helper path used by object detail pages.
3. No page-owned rule duplication
   - `pages/projectItem.py` may pass field values and react to helper results.
   - `pages/projectItem.py` must not re-implement canonical validation rules.
4. Behavioral consistency checks
   - Empty title fails in modal exactly as it fails in full-page editor.
   - Status/date persistence semantics match full-page editor behavior for both entity types.
5. Preservation checks
   - Project save minimum (>=2 linked items), completion gating, and deletion prompt behavior remain unchanged.
   - Calendar and Event detail behavior remain unchanged.
