import streamlit as st
from core.state import init_state
from core.layout import sidebar_file_controls
from core.navigation import render_primary_navigation
from core.calendar_event_form import render_calendar_event_form

st.set_page_config(page_title="Calendar Event", layout="wide")
init_state()
sidebar_file_controls()

render_primary_navigation()

data = st.session_state.data
selected_id = st.session_state.event_view_id
render_calendar_event_form(data, event_index=selected_id, drawer_mode=False, read_only=False)
