# UI Patterns Specification

## List Page Layout
All list pages must follow the same layout pattern.

Required components:
- Page title
- New Item button
- Grouped sections
- Clickable rows that open Detail view

Applies to:
- Calendar
- Actions
- Delegations
- Projects

## Detail Page Layout
All detail pages must follow the Event View pattern.

Required controls:
- Title field
- Date field(s)
- Details / Description field
- Save button
- Delete button
- Back button

Detail pages include:
- Event View
- Action Detail
- Delegation Detail
- Project Detail

## Project List Presentation
Projects are grouped primarily by project status, not by health.

Primary groups:
- Active
- Someday
- Completed

Completed projects are hidden by default unless the user enables Show Completed.

Within Active, projects are grouped by due-date bucket:
- Past Due
- Upcoming
- Floating

Project health is a derived display attribute shown as a badge/label on each Active project row.
Health does not replace status grouping.

## Project / Draft Date Editing UX
Project due-date fields, draft Action due-date fields, and draft Delegation follow-up date fields must be directly and interactively editable when shown.

The UI must not require a separate checkbox to enable date entry.
The checkbox-based date-enable pattern is not allowed for these fields.
