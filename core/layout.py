import hashlib
import json
import streamlit as st
from core.state import init_state
from core.calendar_utils import ensure_event_utc_fields

REQUIRED_LIST_KEYS = ["actions", "calendar", "delegations", "routines"]


def _normalize_loaded_gtd(loaded):
    if not isinstance(loaded, dict):
        loaded = {}

    for key in REQUIRED_LIST_KEYS:
        if key not in loaded or not isinstance(loaded[key], list):
            loaded[key] = []

    for ev in loaded["calendar"]:
        if isinstance(ev, dict):
            ensure_event_utc_fields(ev)

    return loaded


def sidebar_file_controls():
    init_state()
    st.sidebar.title("Session File")

    uploaded = st.sidebar.file_uploader("Upload GTD JSON", type="json")

    if uploaded is not None:
        file_bytes = uploaded.getvalue()
        sig = hashlib.sha256(file_bytes).hexdigest()

        if st.session_state.uploaded_sig != sig:
            loaded = json.loads(file_bytes.decode("utf-8"))
            st.session_state.data = _normalize_loaded_gtd(loaded)
            st.session_state.uploaded_sig = sig
            st.session_state.calendar_edit_index = None
            st.session_state.calendar_new_mode = False
            st.session_state.action_view_index = None
            st.session_state.delegation_view_index = None
            st.sidebar.success("GTD file loaded")

    export_json = json.dumps(st.session_state.data, indent=2)

    st.sidebar.download_button(
        "Download Updated GTD",
        export_json,
        "gtd_updated.json",
        "application/json"
    )
