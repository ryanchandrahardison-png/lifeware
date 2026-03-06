import streamlit as st
from datetime import date, time
from core.state import init_state
from core.layout import sidebar_file_controls
from core.calendar_utils import (
    parse_dt_any,
    ensure_event_utc_fields,
    local_to_utc_iso,
    utc_to_local_parts,
)

st.set_page_config(page_title="Calendar Event", layout="wide")
init_state()
sidebar_file_controls()

st.sidebar.markdown("---")
st.sidebar.page_link("app.py", label="Home", icon="🏠")
st.sidebar.page_link("pages/calendarList.py", label="Calendar", icon="📅")
st.sidebar.page_link("pages/actions.py", label="Actions", icon="✅")
st.sidebar.page_link("pages/delegations.py", label="Delegations", icon="🤝")
st.sidebar.page_link("pages/routines.py", label="Routines", icon="🔁")

data = st.session_state.data

is_edit = (
    st.session_state.calendar_new_mode is False
    and st.session_state.calendar_edit_index is not None
)

title_default = ""
desc_default = ""
status_default = "Scheduled"
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
    ensure_event_utc_fields(ev)

    title_default = ev.get("title", "")
    desc_default = ev.get("description", "")
    status_default = ev.get("status", "Scheduled")

    sdt = parse_dt_any(ev.get("start_utc")) or parse_dt_any(ev.get("start"))
    edt = parse_dt_any(ev.get("end_utc")) or parse_dt_any(ev.get("end"))

    if sdt:
        s_date, s_time = utc_to_local_parts(sdt)
    if edt:
        e_date, e_time = utc_to_local_parts(edt)

st.title("📅 Edit Event" if is_edit else "📅 Add Event")

with st.form("calendar_form"):
    title = st.text_input("Title", value=title_default)

    c1, c2 = st.columns(2)
    start_date = c1.date_input("Start Date", value=s_date)
    start_time = c2.time_input("Start Time", value=s_time)

    c3, c4 = st.columns(2)
    end_date = c3.date_input("End Date", value=e_date)
    end_time = c4.time_input("End Time", value=e_time)

    description = st.text_area("Description", value=desc_default)

    status = st.selectbox(
        "Status",
        ["Scheduled", "Complete"],
        index=0 if status_default != "Complete" else 1,
    )

    confirm_delete = st.checkbox("Confirm deletion") if is_edit else False

    cols = st.columns(3)
    save = cols[0].form_submit_button("Save Changes" if is_edit else "Create Event")
    delete = cols[1].form_submit_button("Delete Event", disabled=not is_edit)
    back = cols[2].form_submit_button("Back to Calendar")

if back:
    st.switch_page("pages/calendarList.py")

if delete and is_edit:
    if not confirm_delete:
        st.error("Confirm deletion first")
    else:
        del data["calendar"][idx]
        st.session_state.calendar_edit_index = None
        st.session_state.calendar_new_mode = False
        st.switch_page("pages/calendarList.py")

if save:
    start_utc = local_to_utc_iso(start_date, start_time)
    end_utc = local_to_utc_iso(end_date, end_time)

    payload = {
        "title": title.strip() or "Untitled Event",
        "description": description.strip(),
        "status": status,
        "start_utc": start_utc,
        "end_utc": end_utc,
        "start": start_utc,
        "end": end_utc,
    }

    if is_edit:
        data["calendar"][idx].update(payload)
    else:
        data["calendar"].append(payload)

    st.session_state.calendar_edit_index = None
    st.session_state.calendar_new_mode = False
    st.switch_page("pages/calendarList.py")
