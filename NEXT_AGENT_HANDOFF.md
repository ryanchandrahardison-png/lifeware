# NEXT_AGENT_HANDOFF

## Role
Developer

## What changed
- Fixed a Project re-entry regression by clearing stale project UI/runtime state before opening Project Details from Projects list and from New Project.
- Added `_reset_project_detail_runtime_state()` in `pages/projects.py` and invoked it in both navigation entry points.
- Updated requirements tracker with a persisted rule that Project Details entry must clear stale runtime flags to prevent layout/modal drift after save/re-open flows.

## Why
- User reported Project Details looked correct during initial create flow, but reverted to older behavior after saving, returning to list, and reopening the project.
- Root cause was stale UI/flag state surviving between Project page entries.

## Validation
- `python -m py_compile pages/projects.py pages/projectItem.py core/project_service.py core/item_detail_form.py`
