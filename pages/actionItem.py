import streamlit as st
from core.state import init_state
from core.layout import sidebar_file_controls
from core.item_detail_form import render_item_detail_form

st.set_page_config(page_title="Action Details", layout="wide")
init_state()
sidebar_file_controls()

st.sidebar.markdown("---")
st.sidebar.page_link("app.py", label="Home", icon="🏠")
st.sidebar.page_link("pages/calendarList.py", label="Calendar", icon="📅")
st.sidebar.page_link("pages/actions.py", label="Actions", icon="✅")
st.sidebar.page_link("pages/delegations.py", label="Delegations", icon="🤝")
st.sidebar.page_link("pages/projects.py", label="Projects", icon="📁")
st.sidebar.page_link("pages/routines.py", label="Routines", icon="🔁")

render_item_detail_form(
    data=st.session_state.data,
    list_key="actions",
    item_id=st.session_state.action_view_id,
    title_emoji="✅",
    page_title="Action Details",
    back_page="pages/actions.py",
    back_label="Back to Actions",
    title_keys=["title"],
    subtitle_text="Edit the selected action and save changes.",
    show_due_date=True,
)
