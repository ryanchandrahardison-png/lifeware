# Routines Feature Specification

## Status
Approved backlog only.
Not approved for the current implementation pass.

## Purpose
Routines provide recurring operating checklists that help the user execute daily and periodic habits without mixing those checklist items into the main Next Actions view.

## Cadence Values
Each routine must have one of these cadence values:
- Daily
- Weekly
- Monthly
- 3-Month
- 6-Month
- Yearly

## Daily Routine Scheduling
Daily routines must include a start time.

## Routine Tasks
Each routine contains a list of tasks.
Routine tasks use the same format as Next Actions, but they are hidden from the main Next Actions view.

## In-Motion Execution Behavior
When a routine is in motion, the system should ask for each task whether the action has been completed with these options:
- Yes
- No
- Postpone

If Postpone is selected, the system must allow the user to enter the time the task will take place.

## Reset Behavior
Routines reset at midnight based on their cadence.

## Approved Initial Routine Set
- Wake Up | Daily | 4:45 AM
- Morning Review | Daily | 5:30 AM
- Mid-Day Review | Daily | 12:00 PM
- Shutdown | Daily | 4:30 PM
- Afternoon | Daily | 5:30 PM
- Bed Time | Daily | 9:30 PM

## Not Yet Architected
The following details require a future Architect pass before implementation:
- canonical routine schema
- recurrence materialization strategy
- history retention
- missed-routine recovery behavior
- midnight reset edge cases
- interaction between routines and calendar/time blocking
- reporting and visibility outside the routine execution surface
