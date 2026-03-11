# SYSTEM_BOOT.md

## Lifeware System Boot

Lifeware is a GTD-based Life Operating System.

Core entities:
- Projects
- Actions
- Delegations
- Calendar Events

Canonical state location:
st.session_state.data

Canonical collections:
events
actions
delegations
projects

All collections are UUID-keyed dictionaries.

## Canonical UI Pattern
All entities follow: List → Detail.
The Event view is the canonical detail layout used by Projects, Actions, and Delegations.

## Current Development Phase
Phase 1 — Projects MVP

Future phases:
Phase 2 — Actions
Phase 3 — Delegations
Phase 4 — Calendar
Phase 5 — Health Indicators
Phase 6 — Automation

## Frozen System Areas
The following must not change unless explicitly approved:
- Calendar behavior
- Event detail structure
- Canonical state storage
- UUID identifiers
- Existing Actions/Delegations list behavior

## UX Rule
Date fields must always be directly editable.
Checkbox-enabled date patterns are forbidden.

## Mutation Governance
Pages render UI.
Pages request mutations.
Pages must not contain business rules.
Mutation logic belongs in shared helpers.

## Developer Workflow
All agents must:
1. Read SYSTEM_BOOT.md first.
2. Then read all other requirement files.
3. Read AI_WORKFLOW_PROMPTS.md.
4. Read AGENT_HANDOFF_SCHEMA.md.
5. Read UI_STATE_ARCHITECTURE.md when work touches Streamlit editor state or widget lifecycle behavior.
6. Read NEXT_AGENT_HANDOFF.md if present.

The boot prompt should only specify the ROLE.
All workflow behavior lives in the requirements package.
Agents must not invent additional workflow processes unless explicitly instructed.

If meaningful work is performed, the agent must produce NEXT_AGENT_HANDOFF.md using AGENT_HANDOFF_SCHEMA.md.

## Reference Documents
ARCHITECTURE.md
DATA_MODEL.md
UI_PATTERNS.md
FEATURE_*.md
MUTATION_RULES.md
REFERENCE_INTEGRITY_RULES.md
DERIVED_VIEW_RULES.md
IMPLEMENTATION_PHASES.md
PRODUCT_BACKLOG.md
AI_DEVELOPER_PROTOCOL.md
AI_WORKFLOW_PROMPTS.md
AGENT_HANDOFF_SCHEMA.md
UI_STATE_ARCHITECTURE.md


## Active Architectural Decision — UI State Architecture

A UI State Architecture refactor has been approved to protect object integrity and prevent Streamlit widget lifecycle defects.

Approved and completed current scope:
Option A — the UI State Architecture has already been applied to `pages/projectItem.py` in the current build stream.

Deferred backlog scope:
Option B — apply the same UI State Architecture later to:
- pages/actionItem.py
- pages/delegationItem.py
- pages/eventItem.py

Completion state rule:
- Option A for `pages/projectItem.py` is COMPLETE and FROZEN.
- Agents must not assign another Developer to re-implement Option A unless a new defect is explicitly opened for that file.
- Agents must not expand Option A into Option B during the current pass unless explicitly approved.


## Task Source Rule

Agents should treat `NEXT_AGENT_HANDOFF.md` as the primary task source for the next agent in the workflow.

Prompts normally only boot the agent; the current role and next task should come from `NEXT_AGENT_HANDOFF.md`.
If a boot prompt includes ROLE text, treat it as a convenience echo of the handoff, not a separate requirement.
The handoff file should define the recommended next role and next step.

Only include a task directly in the prompt when:
- starting a brand new chain with no handoff yet
- intentionally overriding the normal workflow


## Pipeline Autonomy Rule

Agents should operate as a self-propagating pipeline.

Prompts should normally only boot the agent.
`NEXT_AGENT_HANDOFF.md` should provide the task for the next agent.

Only the Architect should normally ask open-ended workflow or design questions.
Developer, Auditor, and QA should continue using the requirements and handoff unless a true architectural conflict or frozen-area violation requires escalation.

Escalation routing rule:
- If Auditor identifies architect-level findings (requirements conflict, architecture drift, frozen-area risk, or phase-boundary ambiguity), Auditor should record them in `NEXT_AGENT_HANDOFF.md` and still route the current build to QA unless the finding is explicitly release-blocking.
- QA must review any carried architect-level findings and determine release readiness. QA may route next to Deployment or to Architect/Architect 2 based on severity and unresolved risk.
- Architect-level findings that are informational or backlog-candidate items must flow forward in handoff notes for Architect triage; they do not automatically block Auditor → QA progression.

If an agent changes requirements, workflow, handoff schema, or boot behavior, the agent must commit those requirement updates and record them in NEXT_AGENT_HANDOFF.md.


## Product Owner Checkpoint Rule
Before the Architect selects the next work item, the Architect must complete a Product Owner backlog check once per Architect pass.

The check may be satisfied in the current pass by either:
- asking the user directly in this pass, or
- using explicit user-provided backlog/requirements guidance already present in the current prompt or handoff context.

This rule is intended to avoid unnecessary Architect-only rounds; when the prompt already includes the user backlog answer (including "no changes"), the Architect should proceed in the same pass.

If the user provides new backlog items or requirement changes, the Architect must classify each item as one of:
- immediate scope
- approved backlog
- deferred future phase
- rejected / not adopted

Only the Architect may merge approved requirement changes into controlled requirement documents.

## Architect Requirement Clarity Rule
When the user provides new or changed requirements, the Architect must ensure the Developer task is unambiguous before assignment.

Required behavior:
- The Architect must not assume unclear intent.
- If requirements are ambiguous and cannot be resolved safely from existing controlled docs/handoff/current user text, the Architect must ask focused clarifying questions before issuing a Developer task.
- Developer-facing handoff instructions must reflect clarified intent as concrete acceptance expectations.

## Decision Freeze Rule
After the Product Owner Checkpoint, the Architect must produce a `DECISION FREEZE` section and mirror it into `NEXT_AGENT_HANDOFF.md`.

The `DECISION FREEZE` must contain:
- current phase
- active scope for the next pass
- explicitly out-of-scope items
- next agent role
- exact next task
- files allowed to change
- files forbidden to change
- whether backlog changed this pass
- required delivery format for the next pass

All non-listed work is out of scope for the next pass.

## Pipeline Completion Rule
If a work item has completed the required pipeline of:
- Architect
- Developer
- Auditor
- QA

then that work item must be treated as:
- COMPLETE
- FROZEN

Architect agents must not assign a new Developer task for that same work item unless:
- a new defect is explicitly opened, or
- the Product Owner explicitly authorizes additional scope.

## Controlled vs Mutable Documents
Controlled requirement documents define architecture, backlog, workflow, and phase rules. They are the architectural source of truth.

Mutable execution-state documents track progress between agents.

Controlled requirement documents:
- SYSTEM_BOOT.md
- lifeware_requirements/AI_WORKFLOW_PROMPTS.md
- lifeware_requirements/AI_DEVELOPER_PROTOCOL.md
- lifeware_requirements/ARCHITECTURE.md
- lifeware_requirements/DATA_MODEL.md
- lifeware_requirements/DERIVED_VIEW_RULES.md
- lifeware_requirements/FEATURE_*.md
- lifeware_requirements/IMPLEMENTATION_PHASES.md
- lifeware_requirements/MUTATION_RULES.md
- lifeware_requirements/PRODUCT_BACKLOG.md
- lifeware_requirements/REFERENCE_INTEGRITY_RULES.md
- lifeware_requirements/REQUIREMENTS_TRACKER.md
- lifeware_requirements/STATE_SCHEMA.md
- lifeware_requirements/UI_PATTERNS.md
- lifeware_requirements/UI_STATE_ARCHITECTURE.md
- lifeware_requirements/AGENT_HANDOFF_SCHEMA.md

Mutable execution-state documents:
- NEXT_AGENT_HANDOFF.md

Default governance:
- Architect may modify controlled requirement documents when the user approves a requirements change.
- Developer, Auditor, and QA should treat controlled requirement documents as read-only unless the user explicitly overrides that rule.
- All agents may update mutable execution-state documents when useful information should be passed forward.


## Newly Approved Backlog Requirement
- Routines / Cadenced Checklists is an approved backlog item and remains out of scope for Phase 1 until explicitly selected by a future Architect DECISION FREEZE.
