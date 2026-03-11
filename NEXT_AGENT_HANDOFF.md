# NEXT_AGENT_HANDOFF

## Role
Developer

## What changed
- Fixed a Streamlit multi-dialog runtime failure in `pages/projectItem.py` when `Add Task`/`Add Delegation` was clicked while a linked-item modal flag was set.
- Removed inline linked-item dialog opening from `_render_linked_items(...)` and deferred dialog opening to one end-of-page dispatch block.
- Cleared linked-item modal state before opening Add Task/Add Delegation dialogs to avoid stale dialog collisions.

## Root cause
- The page could attempt to open two dialogs in one run:
  1) `Linked Item Details` auto-opened during linked-items rendering
  2) `Add Task` / `Add Delegation` opened later in the same run
- Streamlit allows only one first-opened dialog per run, causing `StreamlitAPIException`.

## Behavior now
- Only one dialog opens per run (priority: Add Task, then Add Delegation, else Linked Item Details).
- Project save/delete/back behavior remains unchanged.

## Validation
- `python -m py_compile pages/projectItem.py core/project_service.py pages/projects.py core/item_detail_form.py`
