import streamlit as st
from datetime import datetime, date, time
from zoneinfo import ZoneInfo

st.set_page_config(page_title="Calendar Event", layout="wide")

NY_TZ = ZoneInfo("America/New_York")
UTC_TZ = ZoneInfo("UTC")


# -----------------------------
# Helpers
# -----------------------------
def parse_dt_any(value):
    if not value or not isinstance(value, str):
        return None

    v = value.strip()
    if not v:
        return None

    try:
        iso = v
        if iso.endswith("Z"):
            iso = iso[:-1] + "+00:00"
        dt = datetime.fromisoformat(iso)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC_TZ)
        return dt.astimezone(UTC_TZ)
    except Exception:
        pass

    try:
        dt_local = datetime.strptime(v.upper(), "%d-%b-%Y %H:%M").replace(
            tzinfo=NY_TZ
        )
        return dt_local.astimezone(UTC_TZ)
    except Exception:
        return None


def ensure_event_utc_fields(ev):
    if "start_utc" not in ev or not ev.get("start_utc"):
        dt = parse_dt_any(ev.get("start", ""))
        if dt:
            ev["start_utc"] = dt.isoformat()

    if "end_utc" not in ev or not ev.get("end_utc"):
        dt = parse_dt_any(ev.get("end", ""))
        if dt:
            ev["end_utc"] = dt.isoformat()

    ev.setdefault("start_utc", "")
    ev.setdefault("end_utc", "")


def local_to_utc_iso(d, t):
    dt_local = datetime.combine(d, t).replace(tzinfo=NY_TZ)
    return dt_local.astimezone(UTC_TZ).isoformat()


def utc_to_local_parts(dt):
    dt_local = dt.astimezone(NY_TZ)
    return dt_local.date(), dt_local.time().replace(second=0, microsecond=0)


# -----------------------------
# Guard session state
# -----------------------------
if "data" not in st.session_state:
    st.session_state.data = {
        "actions": [],
        "calendar": [],
        "delegations": [],
        "routines": [],
    }

if "calendar_edit_index" not in st.session_state:
    st.session_state.calendar_edit_index = None

if "calendar_new_mode" not in st.session_state:
    st.session_state.calendar_new_mode = True

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
            st.switch_page("app.py")
        st.stop()

    ev = data["calendar"][idx]
    ensure_event_utc_fields(ev)

    default_title = ev.get("title", "")
    default_desc = ev.get("description", "")
    default_status = ev.get("status", "Scheduled")

    sdt = parse_dt_any(ev.get("start_utc")) or parse_dt_any(ev.get("start"))
    edt = parse_dt_any(ev.get("end_utc")) or parse_dt_any(ev.get("end"))

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
    st.switch_page("app.py")

if delete_clicked and is_edit:
    if not confirm_delete:
        st.error("Confirm deletion first")
    else:
        del data["calendar"][idx]
        st.session_state.calendar_edit_index = None
        st.session_state.calendar_new_mode = False
        st.switch_page("app.py")

if save_clicked:
    start_utc = local_to_utc_iso(start_date, start_time)
    end_utc = local_to_utc_iso(end_date, end_time)

    sdt2 = parse_dt_any(start_utc)
    edt2 = parse_dt_any(end_utc)

    if sdt2 and edt2 and edt2 <= sdt2:
        st.error("End must be after Start.")
    else:
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
        st.switch_page("app.py")