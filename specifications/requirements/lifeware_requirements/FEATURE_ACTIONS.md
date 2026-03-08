# Actions Feature Specification

## Actions List Groups
Actions must be grouped into:
- Past Due
- Upcoming
- Floating

Floating = actions without a due date.

## Action Detail
Fields:
- Title
- Details
- Due Date
- Status

Actions:
- Save
- Delete
- Back

## Visibility Rule
Global Actions list behavior remains unchanged except in later project phases where project-linked actions may appear if `is_active_global = true`.
