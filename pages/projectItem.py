from __future__ import annotations

from copy import deepcopy
from datetime import date

import streamlit as st

from core.entities import (
    action_is_active,
    delegation_is_active,
    is_completed_status,
    linked_actions_for_project,
    linked_delegations_for_project,
    new_uuid,
    parse_date_only,
    project_health,
)
from core.layout import sidebar_file_controls
from core.state import init_state

st.set_page_config(page_title="Project Details", layout="wide")
init_state()
sidebar_file_controls()

st.sidebar.markdown("---")
st.sidebar.page_link("app.py", label="Home", icon="🏠")
st.sidebar.page_link("pages/calendarList.py", label="Calendar", icon="📅")
st.sidebar.page_link("pages/actions.py", label="Actions", icon="✅")
st.sidebar.page_link("pages/delegations.py", label="Delegations", icon="🤝")
st.sidebar.page_link("pages/projects.py", label="Projects", icon="📁")
st.sidebar.page_link("pages/routines.py", label="Routines", icon="🔁")


def empty_draft() -> dict:
    return {
        "title": "",
        "description": "",
        "due_date": None,
        "status": "Active",
        "draft_actions": [],
        "draft_delegations": [],
    }


def completion_ready(linked_actions: list[dict], linked_delegations: list[dict]) -> bool:
    return all(is_completed_status(item.get("status")) for item in linked_actions + linked_delegations)


def draft_linked_count(draft: dict) -> int:
    return len(draft.get("draft_actions", [])) + len(draft.get("draft_delegations", []))


def render_task_rows(items: list[dict], kind: str) -> None:
    if not items:
        st.caption(f"No {kind.lower()} in this section.")
        return
    for item in items:
        st.markdown(f"- **{item.get('title', 'Untitled')}** — {item.get('status', '')}")


def add_draft_action(draft: dict) -> None:
    with st.expander("Add Draft Action"):
        with st.form("add_draft_action_form"):
            title = st.text_input("Action Title")
            due_date_enabled = st.checkbox("Set due date", key="draft_action_due_enabled")
            due_date_value = st.date_input("Action Due Date", value=date.today(), disabled=not due_date_enabled)
            details = st.text_area("Action Details", key="draft_action_details")
            active_global = st.checkbox("Show in global Actions list now", value=False)
            submit = st.form_submit_button("Add Draft Action")
        if submit:
            if not title.strip():
                st.error("Draft action title is required.")
            else:
                draft.setdefault("draft_actions", []).append({
                    "title": title.strip(),
                    "details": details.strip(),
                    "due_date": due_date_value.isoformat() if due_date_enabled else None,
                    "status": "Open",
                    "is_active_global": active_global,
                })
                st.success("Draft action added.")


def add_draft_delegation(draft: dict) -> None:
    with st.expander("Add Draft Delegation"):
        with st.form("add_draft_delegation_form"):
            title = st.text_input("Delegation Title")
            follow_up_enabled = st.checkbox("Set follow-up date", key="draft_delegation_follow_up_enabled")
            follow_up_value = st.date_input("Follow-Up Date", value=date.today(), disabled=not follow_up_enabled)
            details = st.text_area("Delegation Details", key="draft_delegation_details")
            active_global = st.checkbox("Show in global Delegations list now", value=False)
            submit = st.form_submit_button("Add Draft Delegation")
        if submit:
            if not title.strip():
                st.error("Draft delegation title is required.")
            else:
                draft.setdefault("draft_delegations", []).append({
                    "title": title.strip(),
                    "details": details.strip(),
                    "follow_up_date": follow_up_value.isoformat() if follow_up_enabled else None,
                    "status": "Waiting",
                    "is_active_global": active_global,
                })
                st.success("Draft delegation added.")


def save_draft_project(draft: dict) -> bool:
    if draft_linked_count(draft) < 2:
        st.error("A project requires at least 2 linked items total before it can be saved.")
        return False
    if not draft.get("title", "").strip():
        st.error("Project title is required.")
        return False

    data = st.session_state.data
    project_id = new_uuid()
    action_ids = []
    delegation_ids = []

    for action in draft.get("draft_actions", []):
        action_id = new_uuid()
        payload = deepcopy(action)
        payload.update({"id": action_id, "project_id": project_id})
        data["actions"][action_id] = payload
        action_ids.append(action_id)

    for delegation in draft.get("draft_delegations", []):
        delegation_id = new_uuid()
        payload = deepcopy(delegation)
        payload.update({"id": delegation_id, "project_id": project_id})
        data["delegations"][delegation_id] = payload
        delegation_ids.append(delegation_id)

    data["projects"][project_id] = {
        "id": project_id,
        "title": draft["title"].strip(),
        "description": draft.get("description", "").strip(),
        "due_date": draft.get("due_date"),
        "status": draft.get("status", "Active"),
        "action_ids": action_ids,
        "delegation_ids": delegation_ids,
    }
    st.session_state.project_view_id = project_id
    st.session_state.draft_project = None
    st.success("Project saved.")
    return True


def delete_project(project_id: str, choice: str) -> None:
    data = st.session_state.data
    project = data["projects"].get(project_id)
    if not project:
        return

    if choice == "Convert linked items to standalone items":
        for action_id in project.get("action_ids", []):
            if action_id in data["actions"]:
                data["actions"][action_id]["project_id"] = None
                data["actions"][action_id]["is_active_global"] = True
        for delegation_id in project.get("delegation_ids", []):
            if delegation_id in data["delegations"]:
                data["delegations"][delegation_id]["project_id"] = None
                data["delegations"][delegation_id]["is_active_global"] = True
    elif choice == "Delete linked items with the project":
        for action_id in project.get("action_ids", []):
            data["actions"].pop(action_id, None)
        for delegation_id in project.get("delegation_ids", []):
            data["delegations"].pop(delegation_id, None)
    else:
        return

    data["projects"].pop(project_id, None)
    st.session_state.project_view_id = None
    st.session_state.project_delete_mode = None
    st.switch_page("pages/projects.py")


project_id = st.session_state.project_view_id
data = st.session_state.data
is_edit = project_id is not None and project_id in data.get("projects", {})

if not is_edit:
    draft = st.session_state.get("draft_project") or empty_draft()
    st.session_state.draft_project = draft

    st.title("📁 Project Details")
    st.caption("Create a draft project and save it only when it has at least two linked items.")

    with st.form("draft_project_form"):
        title = st.text_input("Title", value=draft.get("title", ""))
        due_enabled = st.checkbox("Set due date", value=bool(draft.get("due_date")))
        due_default = parse_date_only(draft.get("due_date")) or date.today()
        due_date_value = st.date_input("Due Date", value=due_default, disabled=not due_enabled)
        description = st.text_area("Description", value=draft.get("description", ""), height=180)
        status = st.selectbox("Status", ["Active", "Someday"], index=0 if draft.get("status", "Active") == "Active" else 1)
        save = st.form_submit_button("Save")
        back = st.form_submit_button("Back")

    draft["title"] = title
    draft["description"] = description
    draft["status"] = status
    draft["due_date"] = due_date_value.isoformat() if due_enabled else None

    st.markdown(f"**Linked items:** {draft_linked_count(draft)}")
    st.markdown("**Draft Actions**")
    render_task_rows(draft.get("draft_actions", []), "Draft Actions")
    st.markdown("**Draft Delegations**")
    render_task_rows(draft.get("draft_delegations", []), "Draft Delegations")
    add_draft_action(draft)
    add_draft_delegation(draft)

    if back:
        st.session_state.draft_project = None
        st.switch_page("pages/projects.py")
    elif save and save_draft_project(draft):
        st.switch_page("pages/projectItem.py")
else:
    project = data["projects"][project_id]
    linked_actions = linked_actions_for_project(data, project)
    linked_delegations = linked_delegations_for_project(data, project)
    can_complete = completion_ready(linked_actions, linked_delegations)
    st.title("📁 Project Details")
    st.caption(f"Health: {project_health(data, project)}")

    status_options = ["Active", "Someday", "Completed"]
    current_status = project.get("status", "Active")
    default_index = status_options.index(current_status) if current_status in status_options else 0

    with st.form("project_detail_form"):
        title = st.text_input("Title", value=project.get("title", ""))
        due_enabled = st.checkbox("Set due date", value=bool(project.get("due_date")))
        due_default = parse_date_only(project.get("due_date")) or date.today()
        due_date_value = st.date_input("Due Date", value=due_default, disabled=not due_enabled)
        description = st.text_area("Description", value=project.get("description", ""), height=180)
        status = st.selectbox("Status", status_options, index=default_index)
        if status == "Completed" and not can_complete:
            st.caption("Complete Project is disabled until all linked actions and delegations are completed.")
        save = st.form_submit_button("Save")
        delete = st.form_submit_button("Delete")
        back = st.form_submit_button("Back")

    next_actions = [item for item in linked_actions if action_is_active(item)] + [item for item in linked_delegations if delegation_is_active(item)]
    backlog_tasks = [item for item in linked_actions + linked_delegations if item not in next_actions]

    st.markdown("**Next Actions**")
    render_task_rows(next_actions, "Next Actions")
    st.markdown("**Backlog Tasks**")
    render_task_rows(backlog_tasks, "Backlog Tasks")

    if st.session_state.project_delete_mode == project_id:
        st.warning("This project has linked items. Choose how deletion should be handled.")
        choice = st.radio(
            "Deletion behavior",
            [
                "Convert linked items to standalone items",
                "Delete linked items with the project",
                "Cancel deletion",
            ],
            key="project_delete_choice",
        )
        confirm_cols = st.columns(2)
        if confirm_cols[0].button("Confirm Project Delete"):
            if choice == "Cancel deletion":
                st.session_state.project_delete_mode = None
            else:
                delete_project(project_id, choice)
        if confirm_cols[1].button("Back from Delete"):
            st.session_state.project_delete_mode = None

    if back:
        st.session_state.project_view_id = None
        st.session_state.project_delete_mode = None
        st.switch_page("pages/projects.py")
    elif delete:
        if project.get("action_ids") or project.get("delegation_ids"):
            st.session_state.project_delete_mode = project_id
        else:
            data["projects"].pop(project_id, None)
            st.session_state.project_view_id = None
            st.switch_page("pages/projects.py")
    elif save:
        if status == "Completed" and not can_complete:
            st.error("Project cannot be marked Completed until all linked actions and delegations are completed.")
        else:
            project["title"] = title.strip()
            project["description"] = description.strip()
            project["due_date"] = due_date_value.isoformat() if due_enabled else None
            project["status"] = status
            st.success("Project updated.")
