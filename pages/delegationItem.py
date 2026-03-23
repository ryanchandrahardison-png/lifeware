import streamlit as st
from core.layout import bootstrap_page
from core.item_detail_form import render_item_detail_form

bootstrap_page("Delegation Details")

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
)
