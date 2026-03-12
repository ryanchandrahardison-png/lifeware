# PRODUCT_BACKLOG.md

Approved backlog items that are intentionally not part of the current implementation phase.

## Backlog Item: Stalled for 14 Days
### Description
Detect projects that have remained stalled for 14 days and flag them distinctly.

### Definition
A project is stalled when:
- it has incomplete linked items
- it has zero active linked items

If that stalled condition persists for 14 days, display:
- `Stalled (14 days)`

### Purpose
Supports GTD weekly review by surfacing projects that have silently stopped progressing.

### Data Requirements
This feature will require future timestamp tracking, such as:
- `created_at`
- `completed_at`
- `activated_at`
- or project-level `last_progress_at`

These fields must not be added yet in the current MVP phase.

### Phase
Future Phase: Project Intelligence

## Backlog Item: Automatic Next Action Suggestion
### Description
When a project-linked task is completed, the system should offer to activate another backlog item from the same project.

### Purpose
Keeps projects moving, reduces stalled projects, and improves GTD usability.

### Example Prompt
`You completed a task in this project. Would you like to activate another task from the backlog?`

### Phase
Future Phase: Project Intelligence

## Backlog Item: Health-Based Grouping
Optional alternate sorting/filtering by health without replacing status-first grouping.

## Backlog Item: Mutation Ledger
### Description
Record canonical state mutations in a structured mutation ledger.

### Purpose
Supports system integrity, auditability, debugging, undo/redo potential, and future automation.

### Phase
Future Phase: Automation / System Integrity


## Architecture Follow-On Decision
- After Option A stabilization, the next bounded Phase 1 engineering step is to extract project business-rule validation and mutation orchestration into a dedicated state/service layer outside `pages/projectItem.py` while preserving the Option A UI buffer pattern.

## Architecture / Technical Backlog
- Apply UI State Architecture to remaining editor pages:
  - `pages/actionItem.py`
  - `pages/delegationItem.py`
  - `pages/eventItem.py`
  Reason:
  Eliminate the same Streamlit widget lifecycle defect class across the rest of the editor surface after Option A is stabilized in `pages/projectItem.py`.


## UI State Architecture Rollout Decisions

### Option A — Approved Now
Scope:
- `pages/projectItem.py` only

Reason:
- Protect object integrity
- Prevent Streamlit widget lifecycle defects
- Stabilize Phase 1 project flows first

Completion status:
- This work item has already completed the normal pipeline:
  Architect → Developer → Auditor → QA

Execution rule:
- Option A is COMPLETE and FROZEN in the active build stream.
- No new Developer pass may be assigned for Option A unless a new defect is explicitly opened.
- Option B may not begin until a new Architect DECISION FREEZE explicitly authorizes it.

### Option B — Backlog Only
Scope:
- `pages/actionItem.py`
- `pages/delegationItem.py`
- `pages/eventItem.py`

Reason:
- Extend the same UI State Architecture to remaining editor pages after Option A proves stable.

Earliest stage allowed:
- After Option A has completed:
  - architecture planning
  - developer implementation
  - audit review
  - QA review
  - stabilization confirmation in the active build stream

Status:
- Deferred backlog item
- Not approved for current pass


## Backlog Item: Routines / Cadenced Checklists
### Description
Add a routines system for recurring personal operating checklists.

### Cadence Requirements
Each routine must have a cadence of one of:
- Daily
- Weekly
- Monthly
- 3-Month
- 6-Month
- Yearly

### Scheduling Requirements
- Daily routines must have a start time.
- Non-daily routines may support schedule metadata later, but exact timing behavior outside Daily is not yet frozen.

### Routine Task Requirements
- Each routine contains a list of tasks.
- Routine tasks use the same task shape as Next Actions.
- Routine tasks must be hidden from the main Next Actions view unless a later approved design explicitly changes that rule.

### In-Progress Routine Behavior
When a routine is in motion, each routine task must prompt for one of:
- Yes
- No
- Postpone

If the user selects Postpone, the system must allow entry of the time the task will take place.

### Reset Behavior
Routines reset at midnight based on their cadence.

### Approved Initial Routine Set
- Wake Up | Daily | 4:45 AM
- Morning Review | Daily | 5:30 AM
- Mid-Day Review | Daily | 12:00 PM
- Shutdown | Daily | 4:30 PM
- Afternoon | Daily | 5:30 PM
- Bed Time | Daily | 9:30 PM

### Architectural Notes
- Routine state and completion history will require a dedicated future design pass before implementation.
- Reset semantics, carry-forward behavior, missed-routine handling, and history retention are not yet fully architected.
- This feature must not be implemented inside Phase 1 Projects MVP work.

### Phase
Deferred Future Phase: Routines / Personal Operating Cadence

### Status
Approved backlog item


## Backlog Item: Project Detail Backlog Table Layout
### Description
In Project Detail (`pages/projectItem.py` only), place the linked-item review section and Add Task / Add Delegation controls above Save, Delete, and Back.

Render linked items as a table with columns:
- Task Name
- Type
- Date

Date mapping by linked-item type:
- Action → due date
- Delegation → follow-up date

### Product Owner Clarifications (Accepted)
- Applies only to `pages/projectItem.py`.
- Use the order:
  1. Project fields (+ Back available near top)
  2. Linked Items table sections
  3. Add Task / Add Delegation controls
  4. Save / Delete controls
- Include all linked items in the table.
- Group rows by: Completed, Past Due, Upcoming, Floating.
- Sort by date ascending within each non-completed date group.
- Clicking a linked item row opens its detail view.
- Add Task and Add Delegation use modal entry.
- Save/Delete/Back controls should visually match Actions/Delegations detail-page button treatment.
- On narrow/mobile widths, switch the table presentation to stacked rows.

### Purpose
Improve project-review ergonomics by keeping linked-item context and add controls adjacent, and by standardizing linked-item scanability.

### Scope Notes
- This is a presentation/layout backlog item and interaction refinement.
- This does not change canonical data storage or mutation rules.
- Existing completion gating, delete prompt behavior, and date editability rules remain unchanged.

### QA Acceptance Intent
QA should verify each Product Owner clarification item above is implemented.

### Phase
Selected for immediate Phase 1 Architect DECISION FREEZE implementation planning
