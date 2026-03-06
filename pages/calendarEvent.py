import streamlit as st
from datetime import datetime, date, time, timedelta
from core.state import init_state
from core.calendar_utils import (
    ALLOWED_STATUSES,
    DEFAULT_STATUS,
    build_event_payload,
    split_utc_to_local_parts,
)

init_state()
data = st.session_state.data
calendar_events = data.get("calendar", [])

is_edit = (
    st.session_state.calendar_new_mode is False and
    st.session_state.calendar_edit_index is not None and
    0 <= st.session_state.calendar_edit_index < len(calendar_events)
)

idx = st.session_state.calendar_edit_index if is_edit else None

default_title = ""
default_desc = ""
default_status = DEFAULT_STATUS
s_date, s_time = date.today(), time(9, 0)
e_date, e_time = date.today(), time(9, 30)

if is_edit:
    ev = calendar_events[idx]
    default_title = ev.get("title", "")
    default_desc = ev.get("description", "")
    default_status = ev.get("status", DEFAULT_STATUS)

    s_date, s_time = split_utc_to_local_parts(ev.get("start_utc"), s_date, s_time)
    e_date, e_time = split_utc_to_local_parts(ev.get("end_utc"), e_date, e_time)

    if s_date is None:
        s_date = date.today()
    if s_time is None:
        s_time = time(9, 0)
    if e_date is None:
        e_date = s_date
    if e_time is None:
        e_time = (datetime.combine(s_date, s_time) + timedelta(minutes=30)).time().replace(second=0, microsecond=0)

st.title("Edit Event" if is_edit else "Add Event")

with st.form("calendar_form"):
    title = st.text_input("Title", value=default_title)
    description = st.text_area("Description", value=default_desc)

    status = st.selectbox(
        "Status",
        ALLOWED_STATUSES,
        index=ALLOWED_STATUSES.index(default_status) if default_status in ALLOWED_STATUSES else 0,
    )

    time_cols = st.columns(2)
    start_date = time_cols[0].date_input("Start Date", value=s_date)
    start_time = time_cols[0].time_input("Start Time", value=s_time, step=900)
    end_date = time_cols[1].date_input("End Date", value=e_date)
    end_time = time_cols[1].time_input("End Time", value=e_time, step=900)

    if is_edit:
        confirm_delete = st.checkbox("Confirm deletion")
    else:
        confirm_delete = False

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
        del calendar_events[idx]
        st.session_state.calendar_edit_index = None
        st.session_state.calendar_new_mode = False
        st.switch_page("pages/calendarList.py")

if save_clicked:
    payload = build_event_payload(
        title=title,
        description=description,
        status=status,
        start_date=start_date,
        start_time=start_time,
        end_date=end_date,
        end_time=end_time,
    )

    if not payload["title"]:
        st.error("Title is required")
    elif payload["end_utc"] <= payload["start_utc"]:
        st.error("End must be after start")
    else:
        if is_edit:
            calendar_events[idx] = payload
        else:
            calendar_events.append(payload)

        st.session_state.calendar_edit_index = None
        st.session_state.calendar_new_mode = False
        st.switch_page("pages/calendarList.py")
