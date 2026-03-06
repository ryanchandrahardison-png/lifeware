import streamlit as st
from core.state import init_state
from core.layout import sidebar_file_controls
from core.calendar_utils import fmt_ny, parse_dt_any, ensure_event_utc_fields

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

st.title("📅 Calendar")

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

        start_txt = fmt_ny(sdt) if sdt else ev.get("start", "")
        end_txt = fmt_ny(edt) if edt else ev.get("end", "")

        row = st.columns([1, 5, 3, 3, 2])

        if row[0].button("👁", key=f"view_{i}"):
            st.session_state.calendar_edit_index = i
            st.session_state.calendar_new_mode = False
            st.switch_page("pages/calendarEvent.py")

        row[1].write(ev.get("title", ""))
        row[2].write(start_txt)
        row[3].write(end_txt)
        row[4].write(ev.get("status", "Scheduled"))
