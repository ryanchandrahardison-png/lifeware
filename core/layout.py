import json
import streamlit as st
from core.state import init_state
from core.calendar_utils import ensure_event_utc_fields

def sidebar_file_controls():
    init_state()
    st.sidebar.title("Session File")

    uploaded = st.sidebar.file_uploader("Upload GTD JSON", type="json")

    if uploaded is not None:
        file_bytes = uploaded.getvalue()
        sig = (uploaded.name, len(file_bytes))

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
            st.sidebar.success("GTD file loaded")

    export_json = json.dumps(st.session_state.data, indent=2)

    st.sidebar.download_button(
        "Download Updated GTD",
        export_json,
        "gtd_updated.json",
        "application/json"
    )
