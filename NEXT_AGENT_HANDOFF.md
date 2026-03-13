# NEXT AGENT HANDOFF

## Agent Role
Architect

## Timestamp
2026-03-12T22:05:00Z

## Build / Package Reviewed
workspace/lifeware working tree @ HEAD

--------------------------------------------------

## Summary
Reviewed Auditor findings and prepared a bounded Developer remediation packet. Scope is narrowed to three concrete fixes plus one requirements consistency correction already applied in this pass.

--------------------------------------------------

## Current Development Phase
PHASE 1 — Projects MVP Foundation

--------------------------------------------------

## Findings Reviewed (Architect Classification)
1) **Blocking defect**: New Routine pre-persists canonical records before Save in `pages/routineItem.py`.
2) **Medium risk**: Project page still owns linked-item grouping/classification business logic that should move to service/state.
3) **Medium risk**: `save_project_editor_submission(...)` silently coerces malformed `due_date` parse to `None`.
4) **Governance drift**: Option B status text inconsistency in requirements tracker.

--------------------------------------------------

## Requirements Confirmed
- Option B status inconsistency has been corrected in `REQUIREMENTS_TRACKER.md` (now consistently implemented/frozen).
- Project orchestration extraction is complete for save/delete flow entry points, but additional extraction remains for linked-item classification/grouping.

--------------------------------------------------

## Files Reviewed
- NEXT_AGENT_HANDOFF.md
- specifications/requirements/lifeware_requirements/REQUIREMENTS_TRACKER.md
- pages/routineItem.py
- pages/routines.py
- pages/projectItem.py
- core/project_service.py

--------------------------------------------------

## Files Modified
- NEXT_AGENT_HANDOFF.md
- specifications/requirements/lifeware_requirements/REQUIREMENTS_TRACKER.md

--------------------------------------------------

## Developer Execution Packet (Next Pass)
### Task 1 (Blocking) — Routine draft persistence fix
- Prevent canonical routine insertion before user Save.
- `New Routine` should open editor in draft mode without mutating `st.session_state.data["routines"]`.
- On Back from unsaved draft: no routine is created.
- On Save: persist routine exactly once, then return to list view.

### Task 2 (Medium) — Project linked-item business logic extraction
- Move linked-item grouping/classification/filtering helpers out of `pages/projectItem.py` into `core/project_service.py` (or a dedicated project state/service module).
- Page should consume service-returned grouped structures for Next Actions/Backlog rendering.
- Preserve current UX and ordering behavior exactly.

### Task 3 (Medium) — Due-date parse hardening in service orchestration
- In `save_project_editor_submission(...)`, malformed `due_date` must return a validation error (not silent fallback to `None`).
- Ensure valid `None` remains accepted for cleared dates.

### Acceptance checks
- New routine + Back leaves no empty routine persisted.
- New routine + Save persists and returns to list.
- Existing routine edit + Save still returns to list.
- Project save path still enforces due-date rules and completion constraints.
- No Project Detail layout regression.

--------------------------------------------------

## Risks / Watch Areas
- Avoid reopening frozen Option A/Option B behavior beyond targeted fixes.
- Keep routine history/ledger out-of-scope.

--------------------------------------------------

## Escalation Needed
No

--------------------------------------------------

## Recommended Next Agent Role
Developer

--------------------------------------------------

## Recommended Next Action
Implement the three-task remediation packet above in a single bounded pass, then run compile + UI smoke checks for routines and project detail.

--------------------------------------------------

## Smoke Test Focus
- Routines list/detail draft-save-back behavior.
- Project detail linked-item grouping parity after service extraction.
- Project save malformed due-date rejection path.

--------------------------------------------------

## DECISION FREEZE (for next Developer pass)
- active scope: Task 1/2/3 in Developer Execution Packet only
- out-of-scope: history/mutation ledger, new features, layout redesign
- required output: minimal code diff + tests/checks + updated handoff

All non-listed work is out of scope.

--------------------------------------------------

End of handoff
