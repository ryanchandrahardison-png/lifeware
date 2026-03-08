# Requirements Tracker

This document records frozen behavior, architectural decisions, regression-protection rules, and accepted implementation notes.

## Frozen Views
- Calendar view should not change unless explicitly requested by the Product Owner.
- Event view is the canonical detail screen pattern.
- Action and Delegation detail views must follow the same structure.
- Projects should not replace the system's action-centric daily workflow.

## Action-Centric UX Rule
The primary daily working views of the system are:
- Actions
- Delegations
- Calendar

Projects serve as organizational and planning containers, not the primary interface for daily work.

## Architectural Rules
- Canonical data is stored in `st.session_state.data`
- All entities use UUID identifiers
- Canonical collections are UUID-keyed dictionaries
- Projects reference actions and delegations by ID
- Actions and delegations remain top-level canonical collections
- Pages render and request mutations; pages do not own business rules
- Project-specific validation and mutation rules should live in a state/service layer outside `pages/projectItem.py`; the page should orchestrate UI only
- Load-time normalization and integrity repair are accepted safeguards
- Atomic-style save orchestration is acceptable in current phases

## Project Behavior Rules
- Projects have statuses: Someday, Active, Completed
- Completed projects are hidden by default and may be shown with a toggle
- A project is valid only if it has at least 2 linked items total
- Linked items may be any combination of actions and delegations
- Draft project state is editor-only and not persisted until save succeeds
- Project-created draft items remain temporary until save succeeds
- Project completion is blocked until all linked items are completed
- Hidden project tasks remain visible in Project Detail
- Project next actions are linked items where `is_active_global = true`
- Project health is a derived badge/label, not a primary grouping

## Defect Correction Notes
- Load-time event normalization may restore legacy event time fields into canonical event fields so past/historical calendar items remain visible after GTD imports.
- Project due-date editing must work in both draft project creation and saved project editing flows.
- Project, draft action, and draft delegation date fields must be interactively editable when the user chooses to set a date.
- The checkbox-based date-enable pattern is not allowed for these fields.
- A correction pass is not considered complete if the implementation still leaves a date control non-editable in real user interaction.

## Guardrails
- Page files must not remain the long-term home of business rules as the architecture matures.
- No AI implementation pass should begin without following `AI_WORKFLOW_PROMPTS.md`.


## AI Workflow System
- All agents must read `SYSTEM_BOOT.md` first, then all other requirement files.
- `AI_WORKFLOW_PROMPTS.md` is mandatory for Architect, Developer, Auditor, QA, and Architect 2 roles.
- `AGENT_HANDOFF_SCHEMA.md` defines the required handoff file structure.
- Any agent performing meaningful analysis, implementation, audit, or QA must create `NEXT_AGENT_HANDOFF.md` when that information would materially help the next agent avoid drift, rework, or misdiagnosis.
- The required pipeline is Architect → Developer → Auditor → QA → Deployment.
- Architect 2 is an escalation review role for difficult or high-risk changes.
- Developer builds must pass the Pre-Deployment Verification Gate before packaging.
- Every modified Streamlit page must be audited for widget lifecycle safety.
- Defects should be classified before repair to reduce misdiagnosis loops.
- Manual smoke tests are required for project-related Phase 1 changes before deployment.

## UI State Architecture
- UI/editor state for Streamlit pages must use the UI State Architecture defined in `UI_STATE_ARCHITECTURE.md`.
- Option A for `pages/projectItem.py` is approved, completed, and frozen in the current build stream.
- Option B remains in backlog for:
  - `pages/actionItem.py`
  - `pages/delegationItem.py`
  - `pages/eventItem.py`


## Active Architectural Decision — UI State Architecture

## Active Architectural Decision — UI State Architecture

A UI State Architecture refactor has been approved to protect object integrity and prevent Streamlit widget lifecycle defects.

Approved and completed current scope:
Option A — the UI State Architecture has already been applied to `pages/projectItem.py` in the current build stream.

Deferred backlog scope:
Option B — apply the same UI State Architecture later to:
- pages/actionItem.py
- pages/delegationItem.py
- pages/eventItem.py

Agents must treat Option A as the approved and completed architecture change for Phase 1 project defect stabilization.
Agents must not expand Option A into Option B during the current pass unless explicitly approved.


## Task Source Rule
- `NEXT_AGENT_HANDOFF.md` is the primary task source for the next agent in the workflow.
- Prompts should normally specify only the role and boot behavior.
- The handoff should specify the recommended next role and recommended next step.
- Direct prompt tasks should be used only when starting a new chain or intentionally overriding the normal workflow.

## Pipeline Completion Rule
- Any work item that has completed Architect → Developer → Auditor → QA is COMPLETE and FROZEN.
- Architect agents must not assign another Developer to that same work item unless a new defect is explicitly opened or the Product Owner authorizes additional scope.
- Completed items remain architectural precedent, but they are not the next implementation task by default.

## Current Execution Readiness
- The next bounded Phase 1 task is to move project business-rule validation and mutation orchestration into a dedicated state/service layer while keeping `pages/projectItem.py` as a thin UI/controller page.
- Option A for `pages/projectItem.py` has completed Architect → Developer → Auditor → QA in the current build stream.
- Option B remains backlog only and must not start without an explicit new Architect decision freeze.
- Newly approved backlog item: Routines / Cadenced Checklists.
- No additional implementation work is authorized until the Architect selects the next bounded task.


## Developer Artifact Rule
Developer agents must follow the delivery format specified in `NEXT_AGENT_HANDOFF.md`.

Default rule for normal implementation passes:
- provide a minimal diff patch
- provide the full updated project ZIP when code changes

Developers must not ask whether to provide a diff patch vs full replacement when the handoff already specifies the format.
Full-file replacement is allowed only when explicitly required by the handoff or explicitly requested by the user.


## Pipeline Autonomy
- Only the Architect may normally ask open-ended workflow or design questions.
- Developer, Auditor, and QA should derive their task from `NEXT_AGENT_HANDOFF.md` and the requirements package.
- Every non-terminal agent must update `NEXT_AGENT_HANDOFF.md` before finishing.
- If requirements-side files change, the agent must return a regenerated requirements ZIP.
- The intended user workflow is:
  1. download returned ZIP files
  2. open the next agent
  3. paste the universal prompt
  4. let the next agent continue from the handoff


## Routine Backlog Rule
- Routines are approved backlog only in the current baseline.
- Routine tasks use the same format as Next Actions but remain hidden from the main Next Actions view.
- Daily routines must have a start time.
- Routine execution uses task-level responses of Yes, No, or Postpone, with postponed items accepting a target time.
- Routine reset behavior is defined as midnight reset based on cadence.
- Routine implementation requires a future bounded architecture pass and is not authorized during Phase 1 Projects MVP work.
