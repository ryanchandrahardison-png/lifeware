import streamlit as st
from core.calendar_utils import fmt_ny, parse_dt_any, ensure_event_utc_fields

data = st.session_state.data

st.title("Calendar")

top = st.columns([1, 9])

if top[0].button("Add Event"):
    st.session_state.calendar_edit_index = None
    st.session_state.calendar_new_mode = True
    st.switch_page("pages/calendarEvent.py")

if not data["calendar"]:
    st.info("No calendar events.")
else:

    header = st.columns([1, 5, 3, 3, 2])
    header[0].markdown("**View**")
    header[1].markdown("**Title**")
    header[2].markdown("**Start**")
    header[3].markdown("**End**")
    header[4].markdown("**Status**")

    for i, ev in enumerate(data["calendar"]):

        if not isinstance(ev, dict):
            continue

        ensure_event_utc_fields(ev)

        sdt = parse_dt_any(ev.get("start_utc")) or parse_dt_any(ev.get("start"))
        edt = parse_dt_any(ev.get("end_utc")) or parse_dt_any(ev.get("end"))

        start_txt = fmt_ny(sdt) if sdt else ""
        end_txt = fmt_ny(edt) if edt else ""

        row = st.columns([1, 5, 3, 3, 2])

        # 👁 View button beside entry
        if row[0].button("👁", key=f"view_{i}"):
            st.session_state.calendar_edit_index = i
            st.session_state.calendar_new_mode = False
            st.switch_page("pages/calendarEvent.py")

        row[1].write(ev.get("title", ""))
        row[2].write(start_txt)
        row[3].write(end_txt)
        row[4].write(ev.get("status", "Scheduled"))