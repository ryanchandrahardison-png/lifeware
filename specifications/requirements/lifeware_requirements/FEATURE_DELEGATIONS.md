# Delegations Feature Specification

## Delegations List Groups
Delegations must be grouped into:
- Past Due
- Upcoming
- Floating

Floating = delegations without a follow-up date.

## Delegation Detail
Fields:
- Title
- Details
- Follow-Up Date
- Status

Actions:
- Save
- Delete
- Back

## Visibility Rule
Global Delegations list behavior remains unchanged except in later project phases where project-linked delegations may appear if `is_active_global = true`.
