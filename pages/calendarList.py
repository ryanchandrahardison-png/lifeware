import streamlit as st
import pandas as pd
from datetime import datetime
from zoneinfo import ZoneInfo
from core.state import init_state
from core.layout import sidebar_file_controls
from core.selection_utils import selected_single_row_index

st.set_page_config(page_title="Calendar", layout="wide")

init_state()
sidebar_file_controls()

st.sidebar.markdown("---")
st.sidebar.page_link("app.py", label="Home", icon="🏠")
st.sidebar.page_link("pages/calendarList.py", label="Calendar", icon="📅")
st.sidebar.page_link("pages/actions.py", label="Actions", icon="✅")
st.sidebar.page_link("pages/delegations.py", label="Delegations", icon="🤝")
st.sidebar.page_link("pages/projects.py", label="Projects", icon="📁")
st.sidebar.page_link("pages/routines.py", label="Routines", icon="🔁")
st.sidebar.page_link("pages/myDay.py", label="My Day", icon="☀️")

UTC_TZ = ZoneInfo("UTC")

data = st.session_state.data
events = data.get("events", {})

st.title("Calendar")
st.caption("Select a row to view or edit event details.")

if st.button("New Event"):
    st.session_state.event_view_id = None
    st.session_state.event_new_mode = True
    st.switch_page("pages/calendarEvent.py")

st.markdown(
    '''
    <style>
    [data-testid="stDataFrame"] [role="columnheader"][aria-colindex="1"],
    [data-testid="stDataFrame"] [role="gridcell"][aria-colindex="1"] {
        display: none !important;
        width: 0 !important;
        min-width: 0 !important;
        padding: 0 !important;
        border: 0 !important;
    }
    </style>
    ''',
    unsafe_allow_html=True,
)


def parse_dt(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except Exception:
        return None


def sort_key(item):
    event_id, ev = item
    dt = parse_dt(ev.get("start_utc") or "")
    has_dt = dt is not None
    sortable = dt.isoformat() if dt else ""
    return (0 if has_dt else 1, sortable, event_id)


def render_event_table(rows, row_ids, key_suffix):
    if not rows:
        return

    df = pd.DataFrame(rows)

    selection = st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
        key=key_suffix,
    )

    selected_index, had_stale_selection = selected_single_row_index(selection, len(row_ids))
    if had_stale_selection:
        st.session_state.pop(key_suffix, None)
        return
    if selected_index is not None:
        st.session_state.event_view_id = row_ids[selected_index]
        st.session_state.event_new_mode = False
        st.switch_page("pages/calendarEvent.py")


events_sorted = sorted(events.items(), key=sort_key)
now_utc = datetime.now(UTC_TZ)

past_grouped = {}
upcoming_grouped = {}

for event_id, ev in events_sorted:
    dt = parse_dt(ev.get("start_utc"))
    if not dt:
        continue

    target = past_grouped if dt < now_utc else upcoming_grouped
    target.setdefault(dt.date(), []).append((event_id, ev, dt))


if past_grouped:
    st.subheader("Past Events")
    for day in sorted(past_grouped.keys(), reverse=True):
        st.markdown(f"**{day.strftime('%A, %B %d')}**")

        rows = []
        row_ids = []

        for event_id, ev, dt in past_grouped[day]:
            end_dt = parse_dt(ev.get("end_utc"))
            rows.append({
                "Title": ev.get("title", "Untitled"),
                "Start": dt.strftime("%I:%M %p"),
                "End": end_dt.strftime("%I:%M %p") if end_dt else "",
                "Status": ev.get("status", "")
            })
            row_ids.append(event_id)

        render_event_table(rows, row_ids, f"calendar_past_{day.isoformat()}")

if upcoming_grouped:
    st.subheader("Upcoming Events")
    for day in sorted(upcoming_grouped.keys()):
        st.markdown(f"**{day.strftime('%A, %B %d')}**")

        rows = []
        row_ids = []

        for event_id, ev, dt in upcoming_grouped[day]:
            end_dt = parse_dt(ev.get("end_utc"))
            rows.append({
                "Title": ev.get("title", "Untitled"),
                "Start": dt.strftime("%I:%M %p"),
                "End": end_dt.strftime("%I:%M %p") if end_dt else "",
                "Status": ev.get("status", "")
            })
            row_ids.append(event_id)

        render_event_table(rows, row_ids, f"calendar_upcoming_{day.isoformat()}")

if not past_grouped and not upcoming_grouped:
    st.info("No calendar events found in the loaded GTD file.")
