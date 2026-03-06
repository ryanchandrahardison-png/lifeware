import streamlit as st

DEFAULT_DATA = {
    "actions": [],
    "calendar": [],
    "delegations": [],
    "routines": []
}

def init_state():
    if "data" not in st.session_state:
        st.session_state.data = DEFAULT_DATA.copy()

    if "calendar_edit_index" not in st.session_state:
        st.session_state.calendar_edit_index = None

    if "calendar_new_mode" not in st.session_state:
        st.session_state.calendar_new_mode = False

    if "uploaded_sig" not in st.session_state:
        st.session_state.uploaded_sig = None
