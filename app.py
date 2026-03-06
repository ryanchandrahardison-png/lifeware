import streamlit as st
import json
import pandas as pd
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
    if not value or not isinstance(value, str):
        return None

    v = value.strip()

    try:
        iso = v
        if iso.endswith("Z"):
            iso = iso[:-1] + "+00:00"
        dt = datetime.fromisoformat(iso)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC_TZ)
        return dt.astimezone(UTC_TZ)
    except:
        pass

    try:
        dt_local = datetime.strptime(v.upper(), "%d-%b-%Y %H:%M").replace(
            tzinfo=NY_TZ
        )
        return dt_local.astimezone(UTC_TZ)
    except:
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
# Session State
# -----------------------------
if "data" not in st.session_state:
    st.session_state.data = {
        "actions": [],
        "calendar": [],
        "delegations": [],
        "routines": [],
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
    "application/json",
)

st.sidebar.warning("Download before leaving.")


# -----------------------------
# Main Menu
# -----------------------------
st.title("Control Engine")

menu = st.sidebar.radio(
    "Main Menu",
    ["Calendar", "Actions", "Delegations", "Routines"],
)


# =====================================================
# Calendar
# =====================================================
if menu == "Calendar":

    st.header("Calendar")

    top = st.columns([1, 1, 8])

    if top[0].button("Add Event"):
        st.session_state.calendar_mode = "form"
        st.session_state.selected_calendar = None
        st.rerun()

    # -------------------------------------
    # FORM SCREEN
    # -------------------------------------
    if st.session_state.calendar_mode == "form":

        is_edit = st.session_state.selected_calendar is not None

        default_title = ""
        default_desc = ""
        default_status = "Scheduled"
        s_date, s_time = date.today(), time(9, 0)
        e_date, e_time = date.today(), time(9, 30)

        if is_edit:

            idx = st.session_state.selected_calendar
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

        st.subheader("Edit Event" if is_edit else "Add Event")

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
            st.session_state.calendar_mode = "list"
            st.session_state.selected_calendar = None
            st.rerun()

        if delete_clicked and is_edit:
            if not confirm_delete:
                st.error("Confirm deletion first")
            else:
                del data["calendar"][idx]
                st.session_state.calendar_mode = "list"
                st.session_state.selected_calendar = None
                st.rerun()

        if save_clicked:

            start_utc = local_to_utc_iso(start_date, start_time)
            end_utc = local_to_utc_iso(end_date, end_time)

            payload = {
                "title": title,
                "description": description,
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

            st.session_state.calendar_mode = "list"
            st.session_state.selected_calendar = None
            st.rerun()

    # -------------------------------------
    # LIST SCREEN (DATAFRAME)
    # -------------------------------------
    else:

        if not data["calendar"]:
            st.info("No calendar events.")
        else:

            rows = []
            row_map = []

            for i, ev in enumerate(data["calendar"]):

                ensure_event_utc_fields(ev)

                sdt = parse_dt_any(ev.get("start_utc")) or parse_dt_any(ev.get("start"))
                edt = parse_dt_any(ev.get("end_utc")) or parse_dt_any(ev.get("end"))

                rows.append(
                    {
                        "Title": ev.get("title", ""),
                        "Start": fmt_ny(sdt) if sdt else "",
                        "End": fmt_ny(edt) if edt else "",
                        "Status": ev.get("status", "Scheduled"),
                    }
                )

                row_map.append(i)

            df = pd.DataFrame(rows)

            event = st.dataframe(
                df,
                use_container_width=True,
                hide_index=True,
                selection_mode="single-row",
                on_select="rerun",
                key="calendar_df",
            )

            selected = event.selection.rows if event and event.selection else []

            if selected:
                actual_idx = row_map[selected[0]]

                if top[1].button("Open Selected Event"):
                    st.session_state.selected_calendar = actual_idx
                    st.session_state.calendar_mode = "form"
                    st.rerun()
            else:
                top[1].button("Open Selected Event", disabled=True)


# =====================================================
# Actions / Delegations / Routines
# =====================================================
if menu == "Actions":
    st.header("Actions")
    for a in data["actions"]:
        st.write(a.get("title", ""))

if menu == "Delegations":
    st.header("Delegations")
    for d in data["delegations"]:
        st.write(d.get("title", ""))

if menu == "Routines":
    st.header("Routines")
    for r in data["routines"]:
        st.write(r.get("title", ""))


# -----------------------------
# Debug
# -----------------------------
with st.expander("Debug Session Data"):
    st.json(data)