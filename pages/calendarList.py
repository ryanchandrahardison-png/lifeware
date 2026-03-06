import streamlit as st
from core.calendar_utils import fmt_ny, parse_dt_any
from core.state import init_state

init_state()
data = st.session_state.data

st.title("Calendar")

top = st.columns([1, 9])

if top[0].button("Add Event"):
    st.session_state.calendar_edit_index = None
    st.session_state.calendar_new_mode = True
    st.switch_page("pages/calendarEvent.py")

calendar_events = []
for i, ev in enumerate(data["calendar"]):
    if not isinstance(ev, dict):
        continue
    sdt = parse_dt_any(ev.get("start_utc"))
    edt = parse_dt_any(ev.get("end_utc"))
    calendar_events.append((i, ev, sdt, edt))

calendar_events.sort(key=lambda row: row[2].isoformat() if row[2] else "")

if not calendar_events:
    st.info("No calendar events yet. Click Add Event to create one.")
else:
    header = st.columns([1, 5, 3, 3, 2])
    header[0].markdown("**View**")
    header[1].markdown("**Title**")
    header[2].markdown("**Start**")
    header[3].markdown("**End**")
    header[4].markdown("**Status**")

    for i, ev, sdt, edt in calendar_events:
        start_txt = fmt_ny(sdt) if sdt else ""
        end_txt = fmt_ny(edt) if edt else ""

        row = st.columns([1, 5, 3, 3, 2])

        if row[0].button("👁", key=f"view_{i}"):
            st.session_state.calendar_edit_index = i
            st.session_state.calendar_new_mode = False
            st.switch_page("pages/calendarEvent.py")

        row[1].write(ev.get("title", ""))
        row[2].write(start_txt)
        row[3].write(end_txt)
        row[4].write(ev.get("status", "Scheduled"))
