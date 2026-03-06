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


def parse_dt_any(value) -> datetime | None:
    """
    Best-effort parse into an aware UTC datetime.
    Supports:
      - ISO 8601 with offset
      - ISO 8601 with Z
      - ISO without tz (assume UTC)
      - DD-MON-YYYY HH:MM (assume America/New_York)
    """
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


def ensure_event_utc_fields(ev: dict) -> None:
    """
    Ensure keys exist: start_utc/end_utc.
    If we can parse legacy start/end, populate them.
    If not, set blank strings so UI doesn't crash.
    """
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


def local_to_utc_iso(d: date, t: time) -> str:
    dt_local = datetime.combine(d, t).replace(tzinfo=NY_TZ)
    return dt_local.astimezone(UTC_TZ).isoformat()


def utc_to_local_parts(dt_utc: datetime) -> tuple[date, time]:
    dt_local = dt_utc.astimezone(NY_TZ)
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
            if k not in loaded or not isinstance(loaded[k], list):
                loaded[k] = []

        for ev in loaded["calendar"]:
            if isinstance(ev, dict):
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

    top = st.columns([1, 9])
    if top[0].button("Add Event"):
        st.session_state.calendar_mode = "form"
        st.session_state.selected_calendar = None
        st.rerun()

    # -------------------------------------
    # FORM SCREEN (Add/Edit)
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

            sdt = parse_dt_any(ev.get("start_utc", "")) or parse_dt_any(
                ev.get("start", "")
            )
            edt = parse_dt_any(ev.get("end_utc", "")) or parse_dt_any(
                ev.get("end", "")
            )

            if sdt:
                s_date, s_time = utc_to_local_parts(sdt)
            if edt:
                e_date, e_time = utc_to_local_parts(edt)

        st.subheader("Edit Event" if is_edit else "Add Event")

        with st.form("calendar_form"):
            title = st.text_input("Title", value=default_title)

            c1, c2 = st.columns(2)
            start_date = c1.date_input(
                "Start Date",
                value=s_date,
                key="form_start_date",
            )
            start_time = c2.time_input(
                "Start Time",
                value=s_time,
                key="form_start_time",
            )

            c3, c4 = st.columns(2)
            end_date = c3.date_input(
                "End Date",
                value=e_date,
                key="form_end_date",
            )
            end_time = c4.time_input(
                "End Time",
                value=e_time,
                key="form_end_time",
            )

            description = st.text_area("Description", value=default_desc)

            status = st.selectbox(
                "Status",
                ["Scheduled", "Complete"],
                index=0 if default_status != "Complete" else 1,
            )

            submitted = st.form_submit_button(
                "Save Changes" if is_edit else "Create Event"
            )

        if submitted:
            start_utc = local_to_utc_iso(start_date, start_time)
            end_utc = local_to_utc_iso(end_date, end_time)

            sdt2 = parse_dt_any(start_utc)
            edt2 = parse_dt_any(end_utc)
            if sdt2 and edt2 and edt2 <= sdt2:
                st.error("End must be after Start.")
            else:
                payload = {
                    "title": title.strip()
                    or (
                        "Untitled Event"
                        if not is_edit
                        else default_title or "Untitled Event"
                    ),
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

                st.session_state.calendar_mode = "list"
                st.session_state.selected_calendar = None
                st.rerun()

        if is_edit:
            st.divider()
            st.subheader("Danger Zone")
            confirm_delete = st.checkbox(
                "Confirm deletion of this event",
                key="confirm_delete",
            )

            if st.button("Delete Event"):
                if not confirm_delete:
                    st.error("Check confirmation box first.")
                else:
                    del data["calendar"][idx]
                    st.session_state.calendar_mode = "list"
                    st.session_state.selected_calendar = None
                    st.rerun()

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

                sdt = parse_dt_any(ev.get("start_utc", "")) or parse_dt_any(
                    ev.get("start", "")
                )
                edt = parse_dt_any(ev.get("end_utc", "")) or parse_dt_any(
                    ev.get("end", "")
                )

                start_txt = fmt_ny(sdt) if sdt else (ev.get("start", "") or "")
                end_txt = fmt_ny(edt) if edt else (ev.get("end", "") or "")

                row = st.columns([1, 5, 3, 3, 2])

                if row[0].button("👁️", key=f"view{i}"):
                    st.session_state.selected_calendar = i
                    st.session_state.calendar_mode = "form"
                    st.rerun()

                row[1].write(ev.get("title", ""))
                row[2].write(start_txt)
                row[3].write(end_txt)
                row[4].write(ev.get("status", "Scheduled"))


# =====================================================
# Actions / Delegations / Routines
# =====================================================
if menu == "Actions":
    st.header("Actions")
    for a in data["actions"]:
        if isinstance(a, dict):
            st.write(a.get("title", ""))

if menu == "Delegations":
    st.header("Delegations")
    for d in data["delegations"]:
        if isinstance(d, dict):
            st.write(d.get("title", ""))

if menu == "Routines":
    st.header("Routines")
    for r in data["routines"]:
        if isinstance(r, dict):
            st.write(r.get("title", ""))


# -----------------------------
# Debug
# -----------------------------
with st.expander("Debug Session Data"):
    st.json(data)