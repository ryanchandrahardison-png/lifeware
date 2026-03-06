import json
import streamlit as st
from core.state import init_state
from core.layout import sidebar_file_controls

st.set_page_config(page_title="Delegation Details", layout="wide")
init_state()
sidebar_file_controls()

st.sidebar.markdown("---")
st.sidebar.page_link("app.py", label="Home", icon="🏠")
st.sidebar.page_link("pages/calendarList.py", label="Calendar", icon="📅")
st.sidebar.page_link("pages/actions.py", label="Actions", icon="✅")
st.sidebar.page_link("pages/delegations.py", label="Delegations", icon="🤝")
st.sidebar.page_link("pages/routines.py", label="Routines", icon="🔁")

st.title("🤝 Delegation Details")
st.caption("Delegations are currently read-only.")

items = st.session_state.data.get("delegations", [])
index = st.session_state.delegation_view_index

if index is None or not (0 <= index < len(items)):
    st.info("No delegation is selected.")
else:
    item = items[index]
    if isinstance(item, dict):
        title = item.get("title") or item.get("name") or item.get("task") or item.get("item") or "Untitled"
        st.subheader(title)
        for key, value in item.items():
            if isinstance(value, (dict, list)):
                st.markdown(f"**{key}**")
                st.code(json.dumps(value, indent=2), language="json")
            else:
                st.text_input(key.replace("_", " ").title(), value="" if value is None else str(value), disabled=True)
    else:
        st.text_area("Value", value=str(item), height=200, disabled=True)

if st.button("Back to Delegations"):
    st.session_state.delegation_view_index = None
    st.switch_page("pages/delegations.py")
