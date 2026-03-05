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
    """Display UTC datetime in America/New_York in DD-MON-YYYY 24H:MM."""
    dt_local = dt_utc.astimezone(NY_TZ)
    return dt_local.strftime("%d-%b-%Y %H:%M").upper()


def parse_dt_any(value: str) -> datetime | None:
    """
    Best-effort parse of a datetime string.
    Returns an aware datetime in UTC if possible.
    Accepts ISO strings with timezone; 'Z' is supported.
    """
    if not value or not isinstance(value, str):
        return None
    v = value.strip()
    try:
        if v.endswith("Z"):
            v = v[:-1] + "+00:00"
        dt = datetime.fromisoformat(v)
        if dt.tzinfo is None:
            # Assume UTC if tz missing (conservative for storage)
            dt = dt.replace(tzinfo=UTC_TZ)
        return dt.astimezone(UTC_TZ)
    except Exception:
        return None


def ensure_event_utc_fields(ev: dict) -> None:
    """
    Ensure calendar event has start_utc/end_utc ISO strings.
    If only legacy start/end exist, attempt to parse and promote.
    """
    if "start_utc" not in ev:
        dt = parse_dt_any(ev.get("start", ""))
        if dt:
            ev["start_utc"] = dt.isoformat()
    if "end_utc" not in ev:
        dt = parse_dt_any(ev.get("end", ""))
        if dt:
            ev["end_utc"] = dt.isoformat()


def get_event_dt_utc(ev: dict, key: str) -> datetime | None:
    """Return event datetime for key start_utc/end_utc in UTC."""
    dt = parse_dt_any(ev.get(key, ""))
    if dt:
        return dt
    # fallback: parse legacy keys if needed
    legacy_key = "start" if key == "start_utc" else "end"
    return parse_dt_any(ev.get(legacy_key, ""))


def local_to_utc_iso(d: date, t: time) -> str:
    """Convert America/New_York local date+time to UTC ISO string."""
    dt_local = datetime.combine(d, t).replace(tzinfo=NY_TZ)
    dt_utc = dt_local.astimezone(UTC_TZ)
    return dt_utc.isoformat()


# -----------------------------
# Initialize Session State
# -----------------------------
if "data" not in st.session_state:
    st.session_state.data = {
        "actions": [],
        "calendar": [],
        "delegations": [],
        "routines": []
    }

# Selection state for detail views
if "selected_action" not in st.session_state:
    st.session_state.selected_action = None
if "selected_calendar" not in st.session_state:
    st.session_state.selected_calendar = None
if "selected_delegation" not in st.session_state:
    st.session_state.selected_delegation = None
if "selected_routine" not in st.session_state:
    st.session_state.selected_routine = None

# Calendar screen mode: list | detail | add
if "calendar_mode" not in st.session_state:
    st.session_state.calendar_mode = "list"

# Upload signature so we load file only once (prevents overwriting edits)
if "uploaded_sig" not in st.session_state:
    st.session_state.uploaded_sig = None

data = st.session_state.data


# -----------------------------
# Sidebar: Session File
# -----------------------------
st.sidebar.title("Session File")

uploaded_file = st.sidebar.file_uploader("Upload GTD JSON", type="json")

if uploaded_file is not None:
    file_bytes = uploaded_file.getvalue()
    sig = (uploaded_file.name, len(file_bytes))

    # Only load when upload changes (fixes "can't add after upload" issue)
    if st.session_state.uploaded_sig != sig:
        loaded = json.loads(file_bytes.decode("utf-8"))

        # Defensive: ensure keys exist
        for k in ["actions", "calendar", "delegations", "routines"]:
            if k not in loaded or not isinstance(loaded[k], list):
                loaded[k] = []

        # Normalize calendar events to include UTC fields if possible
        for ev in loaded["calendar"]:
            if isinstance(ev, dict):
                ensure_event_utc_fields(ev)

        st.session_state.data = loaded
        data = st.session_state.data

        # Reset selections + calendar mode
        st.session_state.selected_action = None
        st.session_state.selected_calendar = None
        st.session_state.selected_delegation = None
        st.session_state.selected_routine = None
        st.session_state.calendar_mode = "list"

        st.session_state.uploaded_sig = sig
        st.sidebar.success("GTD file loaded")

export_json = json.dumps(data, indent=2)

st.sidebar.download_button(
    label="Download Updated GTD",
    data=export_json,
    file_name="gtd_updated.json",
    mime="application/json"
)

st.sidebar.warning("Remember to download your updated GTD file before leaving.")


# -----------------------------
# Main Menu
# -----------------------------
st.title("Control Engine — Step 2 (Calendar Upgrade)")

menu = st.sidebar.radio(
    "Main Menu",
    ["Calendar", "Actions", "Delegations", "Routines"]
)


# -----------------------------
# Calendar
# -----------------------------
if menu == "Calendar":
    st.header("Calendar")

    # Top button: Add Event (goes to add screen)
    top_cols = st.columns([1, 9])
    if top_cols[0].button("Add Event"):
        st.session_state.calendar_mode = "add"
        st.session_state.selected_calendar = None
        st.rerun()

    # ---- Add Screen ----
    if st.session_state.calendar_mode == "add":
        st.subheader("Add Event")

        with st.form("calendar_add_form"):
            title = st.text_input("Title", placeholder="e.g., 1:1 with Bob")

            # Date/time pickers (display local NY time, store UTC)
            c1, c2 = st.columns(2)
            start_date = c1.date_input("Start Date", value=date.today(), key="add_start_date")
            start_time = c2.time_input("Start Time", value=time(9, 0), key="add_start_time")

            c3, c4 = st.columns(2)
            end_date = c3.date_input("End Date", value=date.today(), key="add_end_date")
            end_time = c4.time_input("End Time", value=time(9, 30), key="add_end_time")

            description = st.text_area("Description", placeholder="Optional notes / agenda")

            submitted = st.form_submit_button("Create Event")

        btn_cols = st.columns([1, 9])
        if btn_cols[0].button("Back to Calendar"):
            st.session_state.calendar_mode = "list"
            st.rerun()

        if submitted:
            start_utc = local_to_utc_iso(start_date, start_time)
            end_utc = local_to_utc_iso(end_date, end_time)

            # Basic validation: end after start
            sdt = parse_dt_any(start_utc)
            edt = parse_dt_any(end_utc)
            if sdt and edt and edt <= sdt:
                st.error("End must be after Start.")
            else:
                data["calendar"].append({
                    "title": title.strip() or "Untitled Event",
                    "description": description.strip(),
                    "status": "Scheduled",
                    # store canonical UTC
                    "start_utc": start_utc,
                    "end_utc": end_utc,
                    # keep legacy fields for readability / compatibility
                    "start": start_utc,
                    "end": end_utc,
                })
                st.session_state.calendar_mode = "list"
                st.rerun()

    # ---- Detail Screen ----
    elif st.session_state.calendar_mode == "detail" and st.session_state.selected_calendar is not None:
        idx = st.session_state.selected_calendar
        item = data["calendar"][idx]
        ensure_event_utc_fields(item)

        st.subheader("Event Detail")

        st.write("Title:", item.get("title", ""))
        st.write("Status:", item.get("status", ""))

        sdt = get_event_dt_utc(item, "start_utc")
        edt = get_event_dt_utc(item, "end_utc")

        st.write("Start (NY):", fmt_ny(sdt) if sdt else item.get("start", ""))
        st.write("End (NY):", fmt_ny(edt) if edt else item.get("end", ""))

        # Show stored UTC too (for audit)
        with st.expander("Stored UTC values"):
            st.write("start_utc:", item.get("start_utc", ""))
            st.write("end_utc:", item.get("end_utc", ""))

        desc = item.get("description", "")
        if desc:
            st.write("Description:")
            st.write(desc)

        col1, col2 = st.columns(2)
        if col1.button("Mark Complete"):
            data["calendar"][idx]["status"] = "Complete"
            st.rerun()

        if col2.button("Back"):
            st.session_state.calendar_mode = "list"
            st.session_state.selected_calendar = None
            st.rerun()

    # ---- List Screen (table) ----
    else:
        st.session_state.calendar_mode = "list"
        st.session_state.selected_calendar = None

        if not data["calendar"]:
            st.info("No calendar items.")
        else:
            # Header row
            h = st.columns([5, 3, 3, 2, 1])
            h[0].markdown("**Title**")
            h[1].markdown("**Start**")
            h[2].markdown("**End**")
            h[3].markdown("**Status**")
            h[4].markdown("**View**")

            # Rows
            for i, item in enumerate(data["calendar"]):
                if not isinstance(item, dict):
                    continue

                ensure_event_utc_fields(item)

                sdt = get_event_dt_utc(item, "start_utc")
                edt = get_event_dt_utc(item, "end_utc")

                start_txt = fmt_ny(sdt) if sdt else (item.get("start", "") or "")
                end_txt = fmt_ny(edt) if edt else (item.get("end", "") or "")

                cols = st.columns([5, 3, 3, 2, 1])
                cols[0].write(item.get("title", "Untitled"))
                cols[1].write(start_txt)
                cols[2].write(end_txt)
                cols[3].write(item.get("status", "Scheduled"))

                if cols[4].button("👁️", key=f"cal_view_{i}"):
                    st.session_state.selected_calendar = i
                    st.session_state.calendar_mode = "detail"
                    st.rerun()


# -----------------------------
# Actions
# -----------------------------
if menu == "Actions":
    st.header("Actions")

    if st.session_state.selected_action is not None:
        idx = st.session_state.selected_action
        action = data["actions"][idx]

        st.subheader("Action Detail")
        st.write("Title:", action.get("title", ""))
        st.write("Context:", action.get("context", ""))
        st.write("Status:", action.get("status", ""))

        col1, col2 = st.columns(2)
        if col1.button("Mark Done"):
            data["actions"][idx]["status"] = "Done"
            st.rerun()

        if col2.button("Back"):
            st.session_state.selected_action = None
            st.rerun()

    else:
        if not data["actions"]:
            st.info("No actions.")
        else:
            for i, item in enumerate(data["actions"]):
                cols = st.columns([6, 2])
                title = item.get("title", "Untitled Action")
                status = item.get("status", "Open")

                if cols[0].button(title, key=f"act_open_{i}"):
                    st.session_state.selected_action = i
                    st.rerun()

                cols[1].write(status)

        st.divider()
        with st.form("add_action"):
            title = st.text_input("Action", placeholder="e.g., Draft stakeholder email")
            context = st.text_input("Context", "@Computer")
            submitted = st.form_submit_button("Add Action")

        if submitted:
            data["actions"].append({
                "title": title.strip() or "Untitled Action",
                "context": context.strip() or "@Computer",
                "status": "Open"
            })
            st.rerun()


# -----------------------------
# Delegations
# -----------------------------
if menu == "Delegations":
    st.header("Delegations")

    if st.session_state.selected_delegation is not None:
        idx = st.session_state.selected_delegation
        item = data["delegations"][idx]

        st.subheader("Delegation Detail")
        st.write("Owner:", item.get("owner", ""))
        st.write("Delegation:", item.get("title", ""))
        st.write("Status:", item.get("status", ""))

        col1, col2 = st.columns(2)
        if col1.button("Mark Received"):
            data["delegations"][idx]["status"] = "Received"
            st.rerun()

        if col2.button("Back"):
            st.session_state.selected_delegation = None
            st.rerun()

    else:
        if not data["delegations"]:
            st.info("No delegations.")
        else:
            for i, item in enumerate(data["delegations"]):
                cols = st.columns([6, 2])

                owner = item.get("owner", "Unknown")
                title = item.get("title", "Untitled Delegation")
                status = item.get("status", "Waiting")
                label = f"{owner} — {title}"

                if cols[0].button(label, key=f"del_open_{i}"):
                    st.session_state.selected_delegation = i
                    st.rerun()

                cols[1].write(status)

        st.divider()
        with st.form("add_delegation"):
            owner = st.text_input("Owner", placeholder="e.g., Vikram")
            title = st.text_input("Delegation", placeholder="e.g., Update deployment checklist")
            submitted = st.form_submit_button("Add Delegation")

        if submitted:
            data["delegations"].append({
                "owner": owner.strip() or "Unknown",
                "title": title.strip() or "Untitled Delegation",
                "status": "Waiting"
            })
            st.rerun()


# -----------------------------
# Routines
# -----------------------------
if menu == "Routines":
    st.header("Routines")

    if st.session_state.selected_routine is not None:
        idx = st.session_state.selected_routine
        item = data["routines"][idx]

        st.subheader("Routine Detail")
        st.write("Cadence:", item.get("cadence", ""))
        st.write("Routine:", item.get("title", ""))
        st.write("Status:", item.get("status", ""))

        col1, col2 = st.columns(2)
        if col1.button("Mark Done"):
            data["routines"][idx]["status"] = "Done"
            st.rerun()

        if col2.button("Back"):
            st.session_state.selected_routine = None
            st.rerun()

    else:
        if not data["routines"]:
            st.info("No routines.")
        else:
            for i, item in enumerate(data["routines"]):
                cols = st.columns([6, 2])

                cadence = item.get("cadence", "Daily")
                title = item.get("title", "Untitled Routine")
                status = item.get("status", "Open")
                label = f"{cadence} — {title}"

                if cols[0].button(label, key=f"rt_open_{i}"):
                    st.session_state.selected_routine = i
                    st.rerun()

                cols[1].write(status)

        st.divider()
        with st.form("add_routine"):
            cadence = st.selectbox(
                "Cadence",
                ["Daily", "Weekly", "Monthly", "Quarterly", "Yearly"]
            )
            title = st.text_input("Routine", placeholder="e.g., Shine sink")
            submitted = st.form_submit_button("Add Routine")

        if submitted:
            data["routines"].append({
                "cadence": cadence,
                "title": title.strip() or "Untitled Routine",
                "status": "Open"
            })
            st.rerun()


# -----------------------------
# Debug Section
# -----------------------------
with st.expander("Debug Session Data"):
    st.json(data)