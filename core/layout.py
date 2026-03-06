import json
import streamlit as st
from core.calendar_utils import normalize_calendar_events


def sidebar_file_controls(data):
    uploaded = st.sidebar.file_uploader("Upload GTD JSON", type="json")

    if uploaded is not None:
        loaded = json.loads(uploaded.getvalue().decode("utf-8"))
        for key in ["actions", "calendar", "delegations", "routines"]:
            if key not in loaded or not isinstance(loaded[key], list):
                loaded[key] = []

        loaded["calendar"] = normalize_calendar_events(loaded["calendar"])
        st.session_state.data = loaded
        data = loaded
        st.sidebar.success("GTD loaded")

    export_json = json.dumps(data, indent=2)

    st.sidebar.download_button(
        "Download Updated GTD",
        export_json,
        "gtd_updated.json",
        "application/json",
    )
