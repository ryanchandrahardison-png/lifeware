from __future__ import annotations

import streamlit as st

from core.calendar_utils import (
    format_ny_time,
    local_ny_date_from_utc,
    now_utc,
    parse_event_dt_utc,
)
from core.layout import bootstrap_page
from core.selection_utils import (
    inject_selection_column_hide_css,
    selectable_table_single_row,
    selected_single_row_index,
)

bootstrap_page("Calendar")

data = st.session_state.data
events = data.get("events", {})

st.title("Calendar")
st.caption("Select a row to view or edit event details.")

if st.button("New Event"):
    st.session_state.event_view_id = None
    st.session_state.event_new_mode = True
    st.switch_page("pages/calendarEvent.py")

inject_selection_column_hide_css()


def sort_key(item: tuple[str, dict]) -> tuple[int, str, str]:
    event_id, ev = item
    dt_utc = parse_event_dt_utc(ev.get("start_utc") or "")
    has_dt = dt_utc is not None
    sortable = dt_utc.isoformat() if dt_utc else ""
    return (0 if has_dt else 1, sortable, event_id)


def render_event_table(rows: list[dict], row_ids: list[str], key_suffix: str) -> None:
    if not rows:
        return

    selection = selectable_table_single_row(rows, key=key_suffix)
    selected_index, had_stale_selection = selected_single_row_index(selection, len(row_ids))
    if had_stale_selection:
        st.session_state.pop(key_suffix, None)
        return
    if selected_index is not None:
        st.session_state.event_view_id = row_ids[selected_index]
        st.session_state.event_new_mode = False
        st.switch_page("pages/calendarEvent.py")


events_sorted = sorted(events.items(), key=sort_key)
current_utc = now_utc()

past_grouped: dict = {}
upcoming_grouped: dict = {}

for event_id, ev in events_sorted:
    start_utc = parse_event_dt_utc(ev.get("start_utc") or ev.get("start"))
    if not start_utc:
        continue

    local_day = local_ny_date_from_utc(start_utc)
    if local_day is None:
        continue

    target = past_grouped if start_utc < current_utc else upcoming_grouped
    target.setdefault(local_day, []).append((event_id, ev, start_utc))


if past_grouped:
    st.subheader("Past Events")
    for day in sorted(past_grouped.keys(), reverse=True):
        st.markdown(f"**{day.strftime('%A, %B %d')}**")

        rows = []
        row_ids = []

        for event_id, ev, start_utc in past_grouped[day]:
            end_utc = parse_event_dt_utc(ev.get("end_utc"))
            rows.append(
                {
                    "Title": ev.get("title", "Untitled"),
                    "Start": format_ny_time(start_utc),
                    "End": format_ny_time(end_utc),
                    "Status": ev.get("status", ""),
                }
            )
            row_ids.append(event_id)

        render_event_table(rows, row_ids, f"calendar_past_{day.isoformat()}")

if upcoming_grouped:
    st.subheader("Upcoming Events")
    for day in sorted(upcoming_grouped.keys()):
        st.markdown(f"**{day.strftime('%A, %B %d')}**")

        rows = []
        row_ids = []

        for event_id, ev, start_utc in upcoming_grouped[day]:
            end_utc = parse_event_dt_utc(ev.get("end_utc"))
            rows.append(
                {
                    "Title": ev.get("title", "Untitled"),
                    "Start": format_ny_time(start_utc),
                    "End": format_ny_time(end_utc),
                    "Status": ev.get("status", ""),
                }
            )
            row_ids.append(event_id)

        render_event_table(rows, row_ids, f"calendar_upcoming_{day.isoformat()}")

if not past_grouped and not upcoming_grouped:
    st.info("No calendar events found in the loaded GTD file.")
