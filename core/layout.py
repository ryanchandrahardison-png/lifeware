import hashlib
import json
import streamlit as st
from core.state import init_state
from core.entities import ensure_integrity, normalize_data


def sidebar_file_controls():
    init_state()
    st.sidebar.title("Session File")

    uploaded = st.sidebar.file_uploader("Upload GTD JSON", type="json")

    if uploaded is not None:
        file_bytes = uploaded.getvalue()
        sig = hashlib.sha256(file_bytes).hexdigest()

        if st.session_state.uploaded_sig != sig:
            loaded = json.loads(file_bytes.decode("utf-8"))
            st.session_state.data = normalize_data(loaded)
            st.session_state.integrity_warnings = ensure_integrity(st.session_state.data)
            st.session_state.uploaded_sig = sig
            st.session_state.event_view_id = None
            st.session_state.event_new_mode = False
            st.session_state.action_view_id = None
            st.session_state.delegation_view_id = None
            st.session_state.project_view_id = None
            st.session_state.project_delete_mode = None
            st.session_state.draft_project = None
            st.sidebar.success("GTD file loaded")

    if st.session_state.get("integrity_warnings"):
        with st.sidebar.expander("Integrity repairs", expanded=False):
            for warning in st.session_state.integrity_warnings:
                st.write(f"- {warning}")

    export_json = json.dumps(st.session_state.data, indent=2)

    st.sidebar.download_button(
        "Download Updated GTD",
        export_json,
        "gtd_updated.json",
        "application/json"
    )
