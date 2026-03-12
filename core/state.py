import streamlit as st

from core.entities import ensure_integrity, normalize_data

DEFAULT_DATA = {
    "events": {},
    "actions": {},
    "delegations": {},
    "projects": {},
    "routines": {},
}


def _initialize_runtime_state() -> None:
    defaults = {
        "event_view_id": None,
        "event_new_mode": False,
        "action_view_id": None,
        "delegation_view_id": None,
        "project_view_id": None,
        "project_delete_mode": None,
        "project_delete_choice": "Convert linked items to standalone items",
        "draft_project": None,
        "uploaded_sig": None,
        "integrity_warnings": [],
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def init_state():
    if "data" not in st.session_state:
        st.session_state.data = DEFAULT_DATA.copy()
    else:
        st.session_state.data = normalize_data(st.session_state.data)

    _initialize_runtime_state()
    st.session_state.integrity_warnings = ensure_integrity(st.session_state.data)
