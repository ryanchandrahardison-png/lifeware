import streamlit as st
from core.state import init_session_state
from core.layout import render_session_sidebar
from core.calendar_utils import parse_dt_any, fmt_ny

init_session_state()
render_session_sidebar()

data = st.session_state.data

st.title("Calendar")

top = st.columns([1, 9])
if top[0].button("Add Event"):
    st.session_state.calendar_edit_index = None
    st.session_state.calendar_new_mode = True
    st.switch_page("pages/calendarEvent.py")

calendar_events = [ev for ev in data["calendar"] if isinstance(ev, dict)]

if not calendar_events:
    st.info("No calendar events yet. Click Add Event to create one.")
else:
    header = st.columns([0.8, 4, 2.4, 2.4, 1.6])
    header[0].markdown("**View**")
    header[1].markdown("**Title**")
    header[2].markdown("**Start**")
    header[3].markdown("**End**")
    header[4].markdown("**Status**")

    for idx, ev in enumerate(calendar_events):
        sdt = parse_dt_any(ev.get("start_utc"))
        edt = parse_dt_any(ev.get("end_utc"))

        row = st.columns([0.8, 4, 2.4, 2.4, 1.6])
        if row[0].button("👁️", key=f"view_event_{idx}"):
            st.session_state.calendar_edit_index = idx
            st.session_state.calendar_new_mode = False
            st.switch_page("pages/calendarEvent.py")

        row[1].write(ev.get("title", ""))
        row[2].write(fmt_ny(sdt) if sdt else "")
        row[3].write(fmt_ny(edt) if edt else "")
        row[4].write(ev.get("status", "Scheduled"))

with st.expander("Debug Session Data"):
    st.json(data)
