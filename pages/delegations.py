import streamlit as st
from core.state import init_session_state
from core.layout import render_session_sidebar

init_session_state()
render_session_sidebar()

data = st.session_state.data

st.title("Delegations")
st.caption("Placeholder page. Next step is separate list and detail workflow, matching Calendar.")

if not data["delegations"]:
    st.info("No delegations.")
else:
    for item in data["delegations"]:
        if isinstance(item, dict):
            title = item.get("title", "")
            owner = item.get("owner", "")
            st.write(f"{owner} — {title}" if owner else title)

with st.expander("Debug Session Data"):
    st.json(data)
