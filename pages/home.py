import streamlit as st
from core.state import init_session_state
from core.layout import render_session_sidebar

init_session_state()
render_session_sidebar()

data = st.session_state.data

st.title("Lifeware Control Engine")
st.caption("Structured starter with separate pages and shared session file handling.")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Calendar", len(data["calendar"]))
c2.metric("Actions", len(data["actions"]))
c3.metric("Delegations", len(data["delegations"]))
c4.metric("Routines", len(data["routines"]))

st.markdown("### Current structure")
st.write("Use the navigation on the left to open Calendar, Calendar Event, Actions, Delegations, or Routines.")

with st.expander("Debug Session Data"):
    st.json(data)
