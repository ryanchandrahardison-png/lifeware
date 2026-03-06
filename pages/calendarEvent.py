import streamlit as st
from core.state import init_state
from core.layout import sidebar_file_controls
from core.calendar_event_form import render_calendar_event_form

st.set_page_config(page_title="Calendar Event", layout="wide")
init_state()
sidebar_file_controls()

st.sidebar.markdown("---")
st.sidebar.page_link("app.py", label="Home", icon="🏠")
st.sidebar.page_link("pages/calendarList.py", label="Calendar", icon="📅")
st.sidebar.page_link("pages/actions.py", label="Actions", icon="✅")
st.sidebar.page_link("pages/delegations.py", label="Delegations", icon="🤝")
st.sidebar.page_link("pages/routines.py", label="Routines", icon="🔁")

data = st.session_state.data
selected_index = st.session_state.calendar_edit_index
render_calendar_event_form(data, event_index=selected_index, drawer_mode=False, read_only=True)
