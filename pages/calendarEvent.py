import streamlit as st
from core.layout import bootstrap_page
from core.calendar_event_form import render_calendar_event_form

bootstrap_page("Calendar Event")

data = st.session_state.data
selected_id = st.session_state.event_view_id
render_calendar_event_form(data, event_index=selected_id, drawer_mode=False, read_only=False)
