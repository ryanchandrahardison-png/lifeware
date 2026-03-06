import streamlit as st
from core.calendar_utils import normalize_calendar_events


def init_state():
    if "data" not in st.session_state:
        st.session_state.data = {
            "actions": [],
            "calendar": [],
            "delegations": [],
            "routines": []
        }

    if "calendar_edit_index" not in st.session_state:
        st.session_state.calendar_edit_index = None

    if "calendar_new_mode" not in st.session_state:
        st.session_state.calendar_new_mode = False

    normalize_calendar_events(st.session_state.data)
