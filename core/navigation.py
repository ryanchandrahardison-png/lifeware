from __future__ import annotations

import streamlit as st

NAV_LINKS = [
    ("app.py", "Home", "🏠"),
    ("pages/calendarList.py", "Calendar", "📅"),
    ("pages/actions.py", "Actions", "✅"),
    ("pages/delegations.py", "Delegations", "🤝"),
    ("pages/projects.py", "Projects", "📁"),
    ("pages/routines.py", "Routines", "🔁"),
    ("pages/myDay.py", "My Day", "☀️"),
]


def render_primary_navigation() -> None:
    st.sidebar.markdown("---")
    for page, label, icon in NAV_LINKS:
        st.sidebar.page_link(page, label=label, icon=icon)
