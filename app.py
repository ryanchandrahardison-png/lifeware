import streamlit as st
import json

st.set_page_config(page_title="Control Engine", layout="wide")

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

data = st.session_state.data


# -----------------------------
# Sidebar: Session File
# -----------------------------
st.sidebar.title("Session File")

uploaded_file = st.sidebar.file_uploader(
    "Upload GTD JSON",
    type="json"
)

if uploaded_file is not None:
    loaded = json.load(uploaded_file)

    # Defensive: ensure keys exist
    for k in ["actions", "calendar", "delegations", "routines"]:
        if k not in loaded or not isinstance(loaded[k], list):
            loaded[k] = []

    st.session_state.data = loaded
    data = st.session_state.data

    # Reset any open detail views when new file loads
    st.session_state.selected_action = None
    st.session_state.selected_calendar = None
    st.session_state.selected_delegation = None
    st.session_state.selected_routine = None

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
st.title("Control Engine — Step 2")

menu = st.sidebar.radio(
    "Main Menu",
    ["Calendar", "Actions", "Delegations", "Routines"]
)


# -----------------------------
# Calendar
# -----------------------------
if menu == "Calendar":

    st.header("Calendar")

    # Detail View
    if st.session_state.selected_calendar is not None:
        idx = st.session_state.selected_calendar
        item = data["calendar"][idx]

        st.subheader("Calendar Item Detail")

        st.write("Title:", item.get("title", ""))
        st.write("Start:", item.get("start", ""))
        st.write("End:", item.get("end", ""))
        st.write("Status:", item.get("status", ""))

        col1, col2 = st.columns(2)

        if col1.button("Mark Complete"):
            data["calendar"][idx]["status"] = "Complete"
            st.rerun()

        if col2.button("Back"):
            st.session_state.selected_calendar = None
            st.rerun()

    # List View
    else:
        if not data["calendar"]:
            st.info("No calendar items.")
        else:
            for i, item in enumerate(data["calendar"]):
                cols = st.columns([6, 2])

                title = item.get("title", "Untitled")
                status = item.get("status", "Scheduled")

                if cols[0].button(title, key=f"cal_open_{i}"):
                    st.session_state.selected_calendar = i
                    st.rerun()

                cols[1].write(status)

        st.divider()

        with st.form("add_calendar"):
            title = st.text_input("Title", placeholder="e.g., 1:1 with Bob")
            start = st.text_input("Start Time", placeholder="e.g., Thu 03/05 09:00 AM")
            end = st.text_input("End Time", placeholder="e.g., Thu 03/05 09:30 AM")

            submitted = st.form_submit_button("Add Meeting")

            if submitted:
                data["calendar"].append({
                    "title": title.strip() or "Untitled Meeting",
                    "start": start.strip(),
                    "end": end.strip(),
                    "status": "Scheduled"
                })
                st.rerun()


# -----------------------------
# Actions
# -----------------------------
if menu == "Actions":

    st.header("Actions")

    # Detail View
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

    # List View
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

    # Detail View
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

    # List View
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

    # Detail View
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

    # List View
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