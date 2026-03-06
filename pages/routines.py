import streamlit as st
from core.state import init_session_state
from core.layout import render_session_sidebar

init_session_state()
render_session_sidebar()

data = st.session_state.data

st.title("Routines")
st.caption("Placeholder page. Next step is separate list and detail workflow, matching Calendar.")

if not data["routines"]:
    st.info("No routines.")
else:
    for item in data["routines"]:
        if isinstance(item, dict):
            cadence = item.get("cadence", "")
            title = item.get("title", "")
            st.write(f"{cadence} — {title}" if cadence else title)

with st.expander("Debug Session Data"):
    st.json(data)
