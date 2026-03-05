import streamlit as st
import json
from datetime import datetime, date, time
from zoneinfo import ZoneInfo

st.set_page_config(page_title="Control Engine", layout="wide")

NY_TZ = ZoneInfo("America/New_York")
UTC_TZ = ZoneInfo("UTC")


# -----------------------------
# Helpers
# -----------------------------
def fmt_ny(dt_utc: datetime) -> str:
    dt_local = dt_utc.astimezone(NY_TZ)
    return dt_local.strftime("%d-%b-%Y %H:%M").upper()


def parse_dt_any(value):
    if not value:
        return None
    try:
        v = value
        if v.endswith("Z"):
            v = v[:-1] + "+00:00"
        dt = datetime.fromisoformat(v)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC_TZ)
        return dt.astimezone(UTC_TZ)
    except:
        return None


def ensure_event_utc_fields(ev):
    if "start_utc" not in ev:
        dt = parse_dt_any(ev.get("start"))
        if dt:
            ev["start_utc"] = dt.isoformat()

    if "end_utc" not in ev:
        dt = parse_dt_any(ev.get("end"))
        if dt:
            ev["end_utc"] = dt.isoformat()


def local_to_utc_iso(d, t):
    dt_local = datetime.combine(d, t).replace(tzinfo=NY_TZ)
    return dt_local.astimezone(UTC_TZ).isoformat()


def utc_to_local_parts(dt):
    dt_local = dt.astimezone(NY_TZ)
    return dt_local.date(), dt_local.time().replace(second=0, microsecond=0)


# -----------------------------
# Session State
# -----------------------------
if "data" not in st.session_state:
    st.session_state.data = {
        "actions": [],
        "calendar": [],
        "delegations": [],
        "routines": []
    }

if "calendar_mode" not in st.session_state:
    st.session_state.calendar_mode = "list"

if "selected_calendar" not in st.session_state:
    st.session_state.selected_calendar = None

if "uploaded_sig" not in st.session_state:
    st.session_state.uploaded_sig = None

data = st.session_state.data


# -----------------------------
# Sidebar File Handling
# -----------------------------
st.sidebar.title("Session File")

uploaded_file = st.sidebar.file_uploader("Upload GTD JSON", type="json")

if uploaded_file is not None:

    file_bytes = uploaded_file.getvalue()
    sig = (uploaded_file.name, len(file_bytes))

    if st.session_state.uploaded_sig != sig:

        loaded = json.loads(file_bytes.decode("utf-8"))

        for k in ["actions", "calendar", "delegations", "routines"]:
            if k not in loaded:
                loaded[k] = []

        for ev in loaded["calendar"]:
            ensure_event_utc_fields(ev)

        st.session_state.data = loaded
        data = loaded

        st.session_state.calendar_mode = "list"
        st.session_state.selected_calendar = None
        st.session_state.uploaded_sig = sig

        st.sidebar.success("GTD file loaded")

export_json = json.dumps(data, indent=2)

st.sidebar.download_button(
    "Download Updated GTD",
    export_json,
    "gtd_updated.json",
    "application/json"
)

st.sidebar.warning("Download before leaving.")


# -----------------------------
# Main Menu
# -----------------------------
st.title("Control Engine")

menu = st.sidebar.radio(
    "Main Menu",
    ["Calendar", "Actions", "Delegations", "Routines"]
)


# =====================================================
# Calendar
# =====================================================
if menu == "Calendar":

    st.header("Calendar")

    top = st.columns([1,9])
    if top[0].button("Add Event"):
        st.session_state.calendar_mode = "form"
        st.session_state.selected_calendar = None
        st.rerun()

    # -------------------------------------
    # FORM SCREEN (Add/Edit)
    # -------------------------------------
    if st.session_state.calendar_mode == "form":

        is_edit = st.session_state.selected_calendar is not None

        if is_edit:
            idx = st.session_state.selected_calendar
            ev = data["calendar"][idx]
            ensure_event_utc_fields(ev)

            sdt = parse_dt_any(ev["start_utc"])
            edt = parse_dt_any(ev["end_utc"])

            s_date, s_time = utc_to_local_parts(sdt)
            e_date, e_time = utc_to_local_parts(edt)

            default_title = ev.get("title","")
            default_desc = ev.get("description","")
            default_status = ev.get("status","Scheduled")

        else:
            default_title = ""
            default_desc = ""
            default_status = "Scheduled"
            s_date = date.today()
            e_date = date.today()
            s_time = time(9,0)
            e_time = time(9,30)

        st.subheader("Edit Event" if is_edit else "Add Event")

        with st.form("calendar_form"):

            title = st.text_input("Title", value=default_title)

            c1,c2 = st.columns(2)
            start_date = c1.date_input("Start Date", value=s_date)
            start_time = c2.time_input("Start Time", value=s_time)

            c3,c4 = st.columns(2)
            end_date = c3.date_input("End Date", value=e_date)
            end_time = c4.time_input("End Time", value=e_time)

            description = st.text_area("Description", value=default_desc)

            status = st.selectbox(
                "Status",
                ["Scheduled","Complete"],
                index=0 if default_status!="Complete" else 1
            )

            submitted = st.form_submit_button(
                "Save Changes" if is_edit else "Create Event"
            )

        if submitted:

            start_utc = local_to_utc_iso(start_date,start_time)
            end_utc = local_to_utc_iso(end_date,end_time)

            payload = {
                "title": title,
                "description": description,
                "status": status,
                "start_utc": start_utc,
                "end_utc": end_utc,
                "start": start_utc,
                "end": end_utc
            }

            if is_edit:
                data["calendar"][idx].update(payload)
            else:
                data["calendar"].append(payload)

            st.session_state.calendar_mode = "list"
            st.session_state.selected_calendar = None
            st.rerun()

        # DELETE EVENT
        if is_edit:

            st.divider()
            st.subheader("Danger Zone")

            confirm_delete = st.checkbox(
                "Confirm deletion of this event"
            )

            if st.button("Delete Event"):

                if confirm_delete:
                    del data["calendar"][idx]

                    st.session_state.calendar_mode = "list"
                    st.session_state.selected_calendar = None

                    st.rerun()
                else:
                    st.error("Check confirmation box first.")

        if st.button("Back to Calendar"):
            st.session_state.calendar_mode = "list"
            st.session_state.selected_calendar = None
            st.rerun()

    # -------------------------------------
    # LIST SCREEN
    # -------------------------------------
    else:

        if not data["calendar"]:
            st.info("No calendar events.")
        else:

            header = st.columns([1,5,3,3,2])

            header[0].markdown("**View**")
            header[1].markdown("**Title**")
            header[2].markdown("**Start**")
            header[3].markdown("**End**")
            header[4].markdown("**Status**")

            for i,ev in enumerate(data["calendar"]):

                ensure_event_utc_fields(ev)

                sdt = parse_dt_any(ev.get("start_utc"))
                edt = parse_dt_any(ev.get("end_utc"))

                start_txt = fmt_ny(sdt) if sdt else ""
                end_txt = fmt_ny(edt) if edt else ""

                row = st.columns([1,5,3,3,2])

                if row[0].button("👁️", key=f"view{i}"):
                    st.session_state.selected_calendar = i
                    st.session_state.calendar_mode = "form"
                    st.rerun()

                row[1].write(ev.get("title",""))
                row[2].write(start_txt)
                row[3].write(end_txt)
                row[4].write(ev.get("status","Scheduled"))


# =====================================================
# Actions
# =====================================================
if menu == "Actions":

    st.header("Actions")

    for a in data["actions"]:
        st.write(a.get("title",""))


# =====================================================
# Delegations
# =====================================================
if menu == "Delegations":

    st.header("Delegations")

    for d in data["delegations"]:
        st.write(d.get("title",""))


# =====================================================
# Routines
# =====================================================
if menu == "Routines":

    st.header("Routines")

    for r in data["routines"]:
        st.write(r.get("title",""))


# -----------------------------
# Debug
# -----------------------------
with st.expander("Debug Session Data"):
    st.json(data)