# Calendar Feature Specification

Calendar behavior is frozen unless explicitly changed by the Product Owner.

## Calendar List
- Grouped by day
- Past events separated from upcoming events
- Row click opens Event Detail

## Event Detail
Fields:
- Title
- Start Time
- End Time
- Details

Actions:
- Save
- Delete
- Back

## Freeze Rule
Calendar view and Event view must not change unless explicitly requested by the Product Owner.

## GTD Import / Load Behavior
Historical and past events must remain visible after GTD imports.

Load-time event normalization may restore legacy event time representations into canonical event fields when necessary to preserve frozen Calendar behavior.
