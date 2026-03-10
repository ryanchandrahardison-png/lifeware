import streamlit as st
from core.state import init_state
from core.layout import sidebar_file_controls
from core.item_detail_form import DELEGATION_STATUS_OPTIONS, FOLLOW_UP_FIELD_CANDIDATES, render_item_detail_form

st.set_page_config(page_title="Delegation Details", layout="wide")
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
    list_key="delegations",
    item_id=st.session_state.delegation_view_id,
    title_emoji="🤝",
    page_title="Delegation Details",
    back_page="pages/projectItem.py" if st.session_state.get("return_to_project_on_back") else "pages/delegations.py",
    back_label="Back to Project" if st.session_state.get("return_to_project_on_back") else "Back to Delegations",
    title_keys=["title"],
    subtitle_text="Edit the selected delegation and save changes.",
    show_due_date=True,
    date_label="Follow Up Date",
    date_field_candidates=FOLLOW_UP_FIELD_CANDIDATES,
    status_options=DELEGATION_STATUS_OPTIONS,
)
