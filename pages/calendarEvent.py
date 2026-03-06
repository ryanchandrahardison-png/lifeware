import streamlit as st
from datetime import date, time
from core.state import init_session_state
from core.layout import render_session_sidebar
from core.calendar_utils import (
    parse_dt_any,
    utc_to_local_parts,
    build_calendar_event_payload,
)

init_session_state()
render_session_sidebar()

data = st.session_state.data
is_edit = (
    st.session_state.calendar_new_mode is False
    and st.session_state.calendar_edit_index is not None
)

default_title = ""
default_desc = ""
default_status = "Scheduled"
s_date, s_time = date.today(), time(9, 0)
e_date, e_time = date.today(), time(9, 30)

if is_edit:
    idx = st.session_state.calendar_edit_index

    if idx >= len(data["calendar"]):
        st.error("Selected event no longer exists.")
        if st.button("Back to Calendar"):
            st.switch_page("pages/calendarList.py")
        st.stop()

    ev = data["calendar"][idx]
    default_title = ev.get("title", "")
    default_desc = ev.get("description", "")
    default_status = ev.get("status", "Scheduled")

    sdt = parse_dt_any(ev.get("start_utc"))
    edt = parse_dt_any(ev.get("end_utc"))

    if sdt:
        s_date, s_time = utc_to_local_parts(sdt)
    if edt:
        e_date, e_time = utc_to_local_parts(edt)

st.title("Edit Event" if is_edit else "Add Event")

with st.form("calendar_form"):
    title = st.text_input("Title", value=default_title)

    c1, c2 = st.columns(2)
    start_date = c1.date_input("Start Date", value=s_date)
    start_time = c2.time_input("Start Time", value=s_time)

    c3, c4 = st.columns(2)
    end_date = c3.date_input("End Date", value=e_date)
    end_time = c4.time_input("End Time", value=e_time)

    description = st.text_area("Description", value=default_desc)

    status = st.selectbox(
        "Status",
        ["Scheduled", "Complete"],
        index=0 if default_status != "Complete" else 1,
    )

    if is_edit:
        confirm_delete = st.checkbox("Confirm deletion")
    else:
        confirm_delete = False

    cols = st.columns(3)
    save_clicked = cols[0].form_submit_button(
        "Save Changes" if is_edit else "Create Event"
    )
    delete_clicked = cols[1].form_submit_button(
        "Delete Event",
        disabled=not is_edit,
    )
    back_clicked = cols[2].form_submit_button("Back to Calendar")

if back_clicked:
    st.switch_page("pages/calendarList.py")

if delete_clicked and is_edit:
    if not confirm_delete:
        st.error("Confirm deletion first")
    else:
        del data["calendar"][idx]
        st.session_state.calendar_edit_index = None
        st.session_state.calendar_new_mode = False
        st.switch_page("pages/calendarList.py")

if save_clicked:
    if not title.strip():
        st.error("Title is required.")
    else:
        payload = build_calendar_event_payload(
            title=title,
            description=description,
            status=status,
            start_date=start_date,
            start_time=start_time,
            end_date=end_date,
            end_time=end_time,
        )

        sdt2 = parse_dt_any(payload["start_utc"])
        edt2 = parse_dt_any(payload["end_utc"])
        if sdt2 and edt2 and edt2 <= sdt2:
            st.error("End must be after Start.")
        else:
            if is_edit:
                data["calendar"][idx] = payload
            else:
                data["calendar"].append(payload)

            st.session_state.calendar_edit_index = None
            st.session_state.calendar_new_mode = False
            st.switch_page("pages/calendarList.py")

with st.expander("Debug Session Data"):
    st.json(data)
