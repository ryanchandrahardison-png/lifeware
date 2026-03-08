# REFERENCE_INTEGRITY_RULES.md

Defines project ↔ action/delegation and normalization integrity rules.

## Bidirectional Integrity
If an action has:
`project_id = X`

Then project X must contain that action ID in:
`project.action_ids`

If a delegation has:
`project_id = X`

Then project X must contain that delegation ID in:
`project.delegation_ids`

## Hidden Project Tasks
A hidden project task is a linked action or delegation with:
`is_active_global = false`

Hidden project tasks:
- must not appear in the global Actions/Delegations lists
- must always appear inside the Project Detail view

## Delete Integrity
If an action is deleted, its ID must be removed from every project reference list containing it.

If a delegation is deleted, its ID must be removed from every project reference list containing it.

## Project Delete Integrity
When a project is deleted, the system must not silently destroy or orphan tasks.

If linked items exist, the user must choose:
1. Convert linked items to standalone
2. Delete linked items with the project
3. Cancel deletion

## Phase Integrity Repair Strategy
Load-time normalization and repair are accepted safeguards.

Accepted repair behaviors include:
- removing missing action IDs from `project.action_ids`
- removing missing delegation IDs from `project.delegation_ids`
- converting project-linked actions/delegations to standalone when their project is missing
- restoring missing reverse links when a valid `project_id` exists

## Event Normalization During Load
The system may normalize legacy event payloads during load so canonical event fields remain usable.

Accepted behaviors include:
- restoring canonical event time fields from legacy representations
- preserving visibility of historical/past calendar events after GTD import
- performing this normalization during initialization before rendering calendar views

## Load-Time Integrity Check
On application load, the system should verify:
- every ID in `project.action_ids` exists in `actions`
- every ID in `project.delegation_ids` exists in `delegations`
- every non-null `action.project_id` points to an existing project
- every non-null `delegation.project_id` points to an existing project

If integrity violations are found, the system must repair them safely or warn the user.
