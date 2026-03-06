import streamlit as st
import pandas as pd
from datetime import datetime
from core.state import init_state
from core.layout import sidebar_file_controls

st.set_page_config(page_title="Calendar", layout="wide")

init_state()
sidebar_file_controls()

st.sidebar.markdown("---")
st.sidebar.page_link("app.py", label="Home", icon="🏠")
st.sidebar.page_link("pages/calendarList.py", label="Calendar", icon="📅")
st.sidebar.page_link("pages/actions.py", label="Actions", icon="✅")
st.sidebar.page_link("pages/delegations.py", label="Delegations", icon="🤝")
st.sidebar.page_link("pages/routines.py", label="Routines", icon="🔁")

data = st.session_state.data
events = data.get("calendar", [])

st.title("Calendar")


def parse_dt(value):
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


events_sorted = sorted(
    enumerate(events),
    key=lambda x: parse_dt(x[1].get("start_utc") or "") or datetime.max
)

grouped = {}

for idx, ev in events_sorted:
    dt = parse_dt(ev.get("start_utc"))
    if not dt:
        continue

    day = dt.date()
    grouped.setdefault(day, []).append((idx, ev, dt))


for day in sorted(grouped.keys()):
    st.subheader(day.strftime("%A, %B %d"))

    rows = []
    row_index = []

    for idx, ev, dt in grouped[day]:
        end_dt = parse_dt(ev.get("end_utc"))
        start_time = dt.strftime("%I:%M %p")
        end_time = end_dt.strftime("%I:%M %p") if end_dt else ""

        rows.append({
            "Title": ev.get("title", "Untitled"),
            "Start": start_time,
            "End": end_time,
            "Status": ev.get("status", "")
        })
        row_index.append(idx)

    if rows:
        df = pd.DataFrame(rows)

        selection = st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            on_select="rerun",
            selection_mode="single-row",
            key=f"calendar_day_{day.isoformat()}"
        )

        selected_rows = selection.selection.get("rows", []) if selection else []
        if selected_rows:
            selected_pos = selected_rows[0]
            st.session_state.calendar_edit_index = row_index[selected_pos]
            st.session_state.calendar_new_mode = False
            st.switch_page("pages/calendarEvent.py")

st.divider()

if st.button("Add Event"):
    st.session_state.calendar_new_mode = True
    st.session_state.calendar_edit_index = None
    st.switch_page("pages/calendarEvent.py")
