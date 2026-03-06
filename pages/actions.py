import streamlit as st
from core.state import init_session_state
from core.layout import render_session_sidebar

init_session_state()
render_session_sidebar()

data = st.session_state.data

st.title("Actions")
st.caption("Placeholder page. Next step is separate list and detail workflow, matching Calendar.")

if not data["actions"]:
    st.info("No actions.")
else:
    for item in data["actions"]:
        if isinstance(item, dict):
            st.write(item.get("title", ""))

with st.expander("Debug Session Data"):
    st.json(data)
