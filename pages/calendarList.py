
import streamlit as st

data = st.session_state.data

st.title("📅 Calendar")

top = st.columns([1,9])

if top[0].button("Add Event"):
    st.session_state.calendar_edit_index = None
    st.session_state.calendar_new_mode = True
    st.switch_page("pages/calendarEvent.py")

if not data["calendar"]:
    st.info("No calendar events.")
else:

    header = st.columns([1,5,3,3,2])
    header[0].markdown("**View**")
    header[1].markdown("**Title**")
    header[2].markdown("**Start**")
    header[3].markdown("**End**")
    header[4].markdown("**Status**")

    for i, ev in enumerate(data["calendar"]):

        row = st.columns([1,5,3,3,2])

        if row[0].button("👁", key=f"view_{i}"):
            st.session_state.calendar_edit_index = i
            st.session_state.calendar_new_mode = False
            st.switch_page("pages/calendarEvent.py")

        row[1].write(ev.get("title",""))
        row[2].write(ev.get("start",""))
        row[3].write(ev.get("end",""))
        row[4].write(ev.get("status","Scheduled"))
