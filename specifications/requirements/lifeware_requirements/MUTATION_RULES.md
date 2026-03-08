# MUTATION_RULES.md

Defines how canonical entities may be created, updated, or deleted.

Pages must never directly modify unrelated collections.

## Creation Rules
All new canonical entities must:
1. Generate a UUID id
2. Insert into the canonical collection
3. Preserve schema fields defined in DATA_MODEL.md

## Update Rules
Updates must:
- modify only the target object
- preserve unknown fields unless explicitly removed

Never rebuild an object from scratch if only editing a subset of fields.

## Project Save Rules
A draft project must not be saved unless it has at least two linked items total.

Draft project-linked actions and delegations must remain temporary until Save Project succeeds.

On successful Save Project, the mutation layer must create:
- the project
- the linked actions
- the linked delegations
- all references between them

## Completion Rules
A project with one or more non-completed linked actions or delegations must not be allowed to transition to `status = Completed`.

This rule must be enforced in mutation logic even if the UI incorrectly enables the control.

## Delete Rules
Deleting entities must maintain referential integrity.

### Deleting Actions
Must also remove the action ID from any `project.action_ids` list.

### Deleting Delegations
Must also remove the delegation ID from any `project.delegation_ids` list.

### Deleting Projects
If the project contains linked items, the user must be prompted:
1. Convert linked items to standalone
2. Delete linked items with the project
3. Cancel deletion

If Convert to standalone is chosen, each linked item must be updated to:
- `project_id = null`
- `is_active_global = true`

Then the project may be deleted.

If Delete linked items is chosen, linked actions/delegations are deleted before deleting the project.

If Cancel is chosen, nothing changes.

## Accepted Phase Implementation Note
Formal transaction abstractions are not required in current phases.

However:
- project save orchestration
- project completion gating
- project deletion handling
- linked-item standalone conversion / deletion

must live in shared mutation helpers rather than page-owned business logic as the architecture matures.

## UI Interaction Note
UI control strategies may not block required field editability.

The checkbox-based date-enable pattern is not allowed for Project due dates, draft Action due dates, or draft Delegation follow-up dates.

A mutation-safe implementation is still non-compliant if the user cannot actually edit required fields in the rendered interface.
