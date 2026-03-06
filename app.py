import streamlit as st
import json
from datetime import datetime
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

if "uploaded_sig" not in st.session_state:
    st.session_state.uploaded_sig = None

if "calendar_edit_index" not in st.session_state:
    st.session_state.calendar_edit_index = None

if "calendar_new_mode" not in st.session_state:
    st.session_state.calendar_new_mode = False

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
        st.session_state.uploaded_sig = sig
        st.session_state.calendar_edit_index = None
        st.session_state.calendar_new_mode = False
        data = st.session_state.data

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
# Calendar List Page
# =====================================================
if menu == "Calendar":
    st.header("Calendar")

    top = st.columns([1, 9])
    if top[0].button("Add Event"):
        st.session_state.calendar_edit_index = None
        st.session_state.calendar_new_mode = True
        st.switch_page("pages/1_Calendar_Event.py")

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

            start_txt = fmt_ny(sdt) if sdt else ""
            end_txt = fmt_ny(edt) if edt else ""

            row = st.columns([1, 5, 3, 3, 2])

            if row[0].button("👁️", key=f"view_{i}"):
                st.session_state.calendar_edit_index = i
                st.session_state.calendar_new_mode = False
                st.switch_page("pages/1_Calendar_Event.py")

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