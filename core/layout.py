import streamlit as st
from core.state import load_uploaded_json_once, export_current_json
from core.calendar_utils import ensure_event_utc_fields


def render_session_sidebar() -> None:
    st.sidebar.title("Session File")

    uploaded_file = st.sidebar.file_uploader("Upload GTD JSON", type="json")
    if uploaded_file is not None:
        if load_uploaded_json_once(uploaded_file):
            for ev in st.session_state.data["calendar"]:
                if isinstance(ev, dict):
                    ensure_event_utc_fields(ev)
            st.sidebar.success("GTD file loaded")

    st.sidebar.download_button(
        "Download Updated GTD",
        export_current_json(),
        "gtd_updated.json",
        "application/json",
    )

    st.sidebar.warning("Download before leaving.")
