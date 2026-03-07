from datetime import date

import pandas as pd
import streamlit as st

from core.entities import parse_date_only, project_health
from core.layout import sidebar_file_controls
from core.state import init_state

st.set_page_config(page_title="Projects", layout="wide")
init_state()
sidebar_file_controls()

st.sidebar.markdown("---")
st.sidebar.page_link("app.py", label="Home", icon="🏠")
st.sidebar.page_link("pages/calendarList.py", label="Calendar", icon="📅")
st.sidebar.page_link("pages/actions.py", label="Actions", icon="✅")
st.sidebar.page_link("pages/delegations.py", label="Delegations", icon="🤝")
st.sidebar.page_link("pages/projects.py", label="Projects", icon="📁")
st.sidebar.page_link("pages/routines.py", label="Routines", icon="🔁")

st.title("📁 Projects")
st.caption("Projects are grouped by status first, then Active projects by due-date bucket.")

show_completed = st.toggle("Show Completed", value=False)

if st.button("New Project"):
    st.session_state.project_view_id = None
    st.session_state.project_delete_mode = None
    st.session_state.draft_project = {
        "title": "",
        "description": "",
        "due_date": None,
        "status": "Active",
        "draft_actions": [],
        "draft_delegations": [],
    }
    st.switch_page("pages/projectItem.py")


def render_project_table(rows, row_ids, key_suffix):
    if not rows:
        return

    selection = st.dataframe(
        pd.DataFrame(rows),
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
        key=key_suffix,
    )
    selected_rows = selection.selection.get("rows", []) if selection else []
    if selected_rows:
        st.session_state.project_view_id = row_ids[selected_rows[0]]
        st.session_state.draft_project = None
        st.switch_page("pages/projectItem.py")


projects = st.session_state.data.get("projects", {})
today = date.today()
active_past_due = []
active_upcoming = []
active_floating = []
someday_rows = []
completed_rows = []

for project_id, project in projects.items():
    row = {
        "Title": project.get("title", "Untitled"),
        "Due": project.get("due_date") or "",
        "Health": project_health(st.session_state.data, project),
        "Status": project.get("status", "Active"),
    }
    status = project.get("status", "Active")
    due_date = parse_date_only(project.get("due_date"))

    if status == "Completed":
        completed_rows.append((project_id, row))
    elif status == "Someday":
        someday_rows.append((project_id, row))
    else:
        if due_date is None:
            active_floating.append((project_id, row))
        elif due_date < today:
            active_past_due.append((project_id, row))
        else:
            active_upcoming.append((project_id, row))

st.subheader("Active")
for label, entries, key in [
    ("Past Due", active_past_due, "projects_active_past_due"),
    ("Upcoming", active_upcoming, "projects_active_upcoming"),
    ("Floating", active_floating, "projects_active_floating"),
]:
    if entries:
        st.markdown(f"**{label}**")
        render_project_table([row for _, row in entries], [pid for pid, _ in entries], key)

if someday_rows:
    st.subheader("Someday")
    render_project_table([row for _, row in someday_rows], [pid for pid, _ in someday_rows], "projects_someday")

if show_completed and completed_rows:
    st.subheader("Completed")
    render_project_table([row for _, row in completed_rows], [pid for pid, _ in completed_rows], "projects_completed")

if not any([active_past_due, active_upcoming, active_floating, someday_rows, completed_rows if show_completed else []]):
    st.info("No projects found in the loaded GTD file.")
