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


def parse_dt_any(value: str) -> datetime | None:
    if not value or not isinstance(value, str):
        return None
    v = value.strip()
    try:
        if v.endswith("Z"):
            v = v[:-1] + "+00:00"
        dt = datetime.fromisoformat(v)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC_TZ)
        return dt.astimezone(UTC_TZ)
    except Exception:
        return None


def ensure_event_utc_fields(ev: dict) -> None:
    if "start_utc" not in ev:
        dt = parse_dt_any(ev.get("start", ""))
        if dt:
            ev["start_utc"] = dt.isoformat()
    if "end_utc" not in ev:
        dt = parse_dt_any(ev.get("end", ""))
        if dt:
            ev["end_utc"] = dt.isoformat()


def get_event_dt_utc(ev: dict, key: str) -> datetime | None:
    dt = parse_dt_any(ev.get(key, ""))
    if dt:
        return dt
    legacy_key = "start" if key == "start_utc" else "end"
    return parse_dt_any(ev.get(legacy_key, ""))


def local_to_utc_iso(d: date, t: time) -> str:
    dt_local = datetime.combine(d, t).replace(tzinfo=NY_TZ)
    return dt_local.astimezone(UTC_TZ).isoformat()


def utc_to_local_parts(dt_utc: datetime) -> tuple[date, time]:
    dt_local = dt_utc.astimezone(NY_TZ)
    return dt_local.date(), dt_local.time().replace(second=0, microsecond=0)


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

# Selection state
if "selected_action" not in st.session_state:
    st.session_state.selected_action = None
if "selected_calendar" not in st.session_state:
    st.session_state.selected_calendar = None
if "selected_delegation" not in st.session_state:
    st.session_state.selected_delegation = None
if "selected_routine" not in st.session_state:
    st.session_state.selected_routine = None

# Calendar mode: list | form
if "calendar_mode" not in st.session_state:
    st.session_state.calendar_mode = "list"

# Upload signature so we load only once
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

    if st.session_state.uploaded_sig != sig:
        loaded = json.loads(file_bytes.decode("utf-8"))

        for k in ["actions", "calendar", "delegations", "routines"]:
            if k not in loaded or not isinstance(loaded[k], list):
                loaded[k] = []

        for ev in loaded["calendar"]:
            if isinstance(ev, dict):
                ensure_event_utc_fields(ev)

        st.session_state.data = loaded
        data = st.session_state.data

        # Reset selections/modes on new file load
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
st.title("Control Engine — Calendar Edit Upgrade")

menu = st.sidebar.radio(
    "Main Menu",
    ["Calendar", "Actions", "Delegations", "Routines"]
)


# -----------------------------
# Calendar
# -----------------------------
if menu == "Calendar":
    st.header("Calendar")

    top_cols = st.columns([1, 9])
    if top_cols[0].button("Add Event"):
        st.session_state.selected_calendar = None
        st.session_state.calendar_mode = "form"
        st.rerun()

    # -------------------------
    # Unified Add/Edit Form
    # -------------------------
            # ---- Delete (edit mode only) ----
        if is_edit:
            st.divider()
            st.subheader("Danger Zone")

            confirm_delete = st.checkbox("I understand this will permanently delete the event.", key="confirm_delete")

            del_cols = st.columns([2, 8])
            if del_cols[0].button("Delete Event"):
                if not confirm_delete:
                    st.error("Please confirm deletion first.")
                else:
                    # Delete and return to list
                    del data["calendar"][idx]
                    st.session_state.calendar_mode = "list"
                    st.session_state.selected_calendar = None
                    # Reset checkbox so it doesn't stay checked
                    st.session_state.confirm_delete = False
                    st.rerun()

        b1, b2 = st.columns([1, 9])
        if b1.button("Back to Calendar"):
            st.session_state.calendar_mode = "list"
            st.session_state.selected_calendar = None
            st.rerun()

        if submitted:
            start_utc = local_to_utc_iso(start_date, start_time)
            end_utc = local_to_utc_iso(end_date, end_time)

            sdt2 = parse_dt_any(start_utc)
            edt2 = parse_dt_any(end_utc)
            if sdt2 and edt2 and edt2 <= sdt2:
                st.error("End must be after Start.")
            else:
                payload = {
                    "title": title.strip() or ("Untitled Event" if not is_edit else default_title or "Untitled Event"),
                    "description": description.strip(),
                    "status": status,
                    "start_utc": start_utc,
                    "end_utc": end_utc,
                    # legacy fields (kept for compatibility / readability)
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

    # -------------------------
    # List Screen (table)
    # -------------------------
    else:
        st.session_state.calendar_mode = "list"
        st.session_state.selected_calendar = None

        if not data["calendar"]:
            st.info("No calendar items.")
        else:
            # Header row: View | Title | Start | End | Status
            h = st.columns([1, 5, 3, 3, 2])
            h[0].markdown("**View**")
            h[1].markdown("**Title**")
            h[2].markdown("**Start**")
            h[3].markdown("**End**")
            h[4].markdown("**Status**")

            for i, item in enumerate(data["calendar"]):
                if not isinstance(item, dict):
                    continue

                ensure_event_utc_fields(item)

                sdt = get_event_dt_utc(item, "start_utc")
                edt = get_event_dt_utc(item, "end_utc")

                start_txt = fmt_ny(sdt) if sdt else (item.get("start", "") or "")
                end_txt = fmt_ny(edt) if edt else (item.get("end", "") or "")

                cols = st.columns([1, 5, 3, 3, 2])

                if cols[0].button("👁️", key=f"cal_view_{i}"):
                    st.session_state.selected_calendar = i
                    st.session_state.calendar_mode = "form"
                    st.rerun()

                cols[1].write(item.get("title", "Untitled"))
                cols[2].write(start_txt)
                cols[3].write(end_txt)
                cols[4].write(item.get("status", "Scheduled"))


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
            cadence = st.selectbox("Cadence", ["Daily", "Weekly", "Monthly", "Quarterly", "Yearly"])
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