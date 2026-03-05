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

if "selected_action" not in st.session_state:
    st.session_state.selected_action = None

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
    st.session_state.data = loaded
    data = st.session_state.data
    st.sidebar.success("GTD file loaded")

export_json = json.dumps(data, indent=2)

st.sidebar.download_button(
    label="Download Updated GTD",
    data=export_json,
    file_name="gtd_updated.json",
    mime="application/json"
)

st.sidebar.warning(
    "Remember to download your updated GTD file before leaving."
)


# -----------------------------
# Main Menu
# -----------------------------
st.title("Control Engine — Step 1")

menu = st.sidebar.radio(
    "Main Menu",
    ["Calendar", "Actions", "Delegations", "Routines"]
)


# -----------------------------
# Calendar
# -----------------------------
if menu == "Calendar":

    st.header("Calendar")

    for i, item in enumerate(data["calendar"]):

        cols = st.columns([6,2,2])

        cols[0].write(f"**{item['title']}**")
        cols[1].write(item["status"])

        if cols[2].button("Complete", key=f"cal_{i}"):
            data["calendar"][i]["status"] = "Complete"
            st.rerun()

    st.divider()

    with st.form("add_calendar"):

        title = st.text_input("Title")
        start = st.text_input("Start Time")
        end = st.text_input("End Time")

        submitted = st.form_submit_button("Add Meeting")

        if submitted:

            data["calendar"].append({
                "title": title,
                "start": start,
                "end": end,
                "status": "Scheduled"
            })

            st.rerun()


# -----------------------------
# Actions
# -----------------------------
if menu == "Actions":

    st.header("Actions")

    # -------------------------
    # Detail View
    # -------------------------
    if st.session_state.selected_action is not None:

        idx = st.session_state.selected_action
        action = data["actions"][idx]

        st.subheader("Action Detail")

        st.write("Title:", action["title"])
        st.write("Context:", action["context"])
        st.write("Status:", action["status"])

        col1, col2 = st.columns(2)

        if col1.button("Mark Done"):
            data["actions"][idx]["status"] = "Done"
            st.rerun()

        if col2.button("Back"):
            st.session_state.selected_action = None
            st.rerun()

    # -------------------------
    # List View
    # -------------------------
    else:

        for i, item in enumerate(data["actions"]):

            cols = st.columns([6,2])

            if cols[0].button(item["title"], key=f"act_open_{i}"):
                st.session_state.selected_action = i
                st.rerun()

            cols[1].write(item["status"])

        st.divider()

        with st.form("add_action"):

            title = st.text_input("Action")
            context = st.text_input("Context", "@Computer")

            submitted = st.form_submit_button("Add Action")

            if submitted:

                data["actions"].append({
                    "title": title,
                    "context": context,
                    "status": "Open"
                })

                st.rerun()


# -----------------------------
# Delegations
# -----------------------------
if menu == "Delegations":

    st.header("Delegations")

    for i, item in enumerate(data["delegations"]):

        cols = st.columns([6,2,2])

        cols[0].write(f"**{item['owner']} — {item['title']}**")
        cols[1].write(item["status"])

        if cols[2].button("Received", key=f"del_{i}"):
            data["delegations"][i]["status"] = "Received"
            st.rerun()

    st.divider()

    with st.form("add_delegation"):

        owner = st.text_input("Owner")
        title = st.text_input("Delegation")

        submitted = st.form_submit_button("Add Delegation")

        if submitted:

            data["delegations"].append({
                "owner": owner,
                "title": title,
                "status": "Waiting"
            })

            st.rerun()


# -----------------------------
# Routines
# -----------------------------
if menu == "Routines":

    st.header("Routines")

    for i, item in enumerate(data["routines"]):

        cols = st.columns([6,2,2])

        cols[0].write(f"**{item['cadence']} — {item['title']}**")
        cols[1].write(item["status"])

        if cols[2].button("Done", key=f"routine_{i}"):
            data["routines"][i]["status"] = "Done"
            st.rerun()

    st.divider()

    with st.form("add_routine"):

        cadence = st.selectbox(
            "Cadence",
            ["Daily", "Weekly", "Monthly", "Quarterly", "Yearly"]
        )

        title = st.text_input("Routine")

        submitted = st.form_submit_button("Add Routine")

        if submitted:

            data["routines"].append({
                "cadence": cadence,
                "title": title,
                "status": "Open"
            })

            st.rerun()


# -----------------------------
# Debug Section
# -----------------------------
with st.expander("Debug Session Data"):
    st.json(data)