import streamlit as st
from datetime import date, time
from core.calendar_utils import (
    build_calendar_event_payload,
    utc_to_local_parts,
)
from core.state import init_state

init_state()
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
    ev = data["calendar"][idx]

    default_title = ev.get("title", "")
    default_desc = ev.get("description", "")
    default_status = ev.get("status", "Scheduled")

    local_start_date, local_start_time = utc_to_local_parts(ev.get("start_utc"))
    local_end_date, local_end_time = utc_to_local_parts(ev.get("end_utc"))

    if local_start_date and local_start_time:
        s_date, s_time = local_start_date, local_start_time
    if local_end_date and local_end_time:
        e_date, e_time = local_end_date, local_end_time

st.title("Edit Event" if is_edit else "Add Event")

with st.form("calendar_form"):
    title = st.text_input("Title", value=default_title)
    description = st.text_area("Description", value=default_desc)
    status = st.selectbox(
        "Status",
        ["Scheduled", "Complete"],
        index=0 if default_status != "Complete" else 1,
    )

    time_cols_1 = st.columns(2)
    start_date = time_cols_1[0].date_input("Start Date", value=s_date)
    start_time = time_cols_1[1].time_input("Start Time", value=s_time)

    time_cols_2 = st.columns(2)
    end_date = time_cols_2[0].date_input("End Date", value=e_date)
    end_time = time_cols_2[1].time_input("End Time", value=e_time)

    confirm_delete = st.checkbox("Confirm deletion") if is_edit else False

    cols = st.columns(3)
    save_clicked = cols[0].form_submit_button("Save Changes" if is_edit else "Create Event")
    delete_clicked = cols[1].form_submit_button("Delete Event", disabled=not is_edit)
    back_clicked = cols[2].form_submit_button("Back to Calendar")

if back_clicked:
    st.switch_page("pages/calendarList.py")

if delete_clicked and is_edit:
    if not confirm_delete:
        st.error("Confirm deletion first")
    else:
        del data["calendar"][idx]
        st.switch_page("pages/calendarList.py")

if save_clicked:
    if not title.strip():
        st.error("Title is required")
    else:
        start_iso = build_calendar_event_payload("x", "", status, start_date, start_time, end_date, end_time)["start_utc"]
        end_iso = build_calendar_event_payload("x", "", status, start_date, start_time, end_date, end_time)["end_utc"]
        if start_iso >= end_iso:
            st.error("End must be after start")
        else:
            payload = build_calendar_event_payload(
                title,
                description,
                status,
                start_date,
                start_time,
                end_date,
                end_time,
            )
            if is_edit:
                data["calendar"][idx] = payload
            else:
                data["calendar"].append(payload)
            st.switch_page("pages/calendarList.py")
