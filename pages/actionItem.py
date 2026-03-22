import streamlit as st
from core.state import init_state
from core.layout import sidebar_file_controls
from core.navigation import render_primary_navigation
from core.item_detail_form import render_item_detail_form

st.set_page_config(page_title="Action Details", layout="wide")
init_state()
sidebar_file_controls()

render_primary_navigation()

render_item_detail_form(
    data=st.session_state.data,
    list_key="actions",
    item_id=st.session_state.action_view_id,
    title_emoji="✅",
    page_title="Action Details",
    back_page="pages/projectItem.py" if st.session_state.get("return_to_project_on_back") else "pages/actions.py",
    back_label="Back to Project" if st.session_state.get("return_to_project_on_back") else "Back to Actions",
    title_keys=["title"],
    subtitle_text="Edit the selected action and save changes.",
    show_due_date=True,
)
