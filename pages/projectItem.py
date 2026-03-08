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


def render_task_rows(items: list[dict], kind: str, *, date_field: str | None = None, date_label: str = "Date") -> None:
    if not items:
        st.caption(f"No {kind.lower()} in this section.")
        return
    for item in items:
        parts = [f"**{item.get('title', 'Untitled')}**", str(item.get("status", ""))]
        if date_field and item.get(date_field):
            parts.append(f"{date_label}: {item.get(date_field)}")
        st.markdown("- " + " — ".join([part for part in parts if part]))


def _toggle_key(prefix: str, suffix: str) -> str:
    return f"{prefix}_{suffix}_enabled"


def _set_editor_defaults(prefix: str, values: dict) -> None:
    for key, value in values.items():
        st.session_state.setdefault(f"{prefix}_{key}", value)


def _reset_editor_state(prefix: str, defaults: dict) -> None:
    for key, value in defaults.items():
        st.session_state[f"{prefix}_{key}"] = value


def _append_draft_action(draft: dict, item: dict) -> None:
    draft.setdefault("draft_actions", []).append(item)


def _append_draft_delegation(draft: dict, item: dict) -> None:
    draft.setdefault("draft_delegations", []).append(item)


def add_draft_action(draft: dict, *, prefix: str = "draft_action", submit_label: str = "Add Draft Action") -> None:
    editor_defaults = {
        "title": "",
        "details": "",
        "date": date.today(),
        "active_global": False,
    }
    _set_editor_defaults(prefix, editor_defaults)
    due_enabled = st.checkbox(
        "Set due date",
        value=bool(st.session_state.get(_toggle_key(prefix, "due_date"), False)),
        key=_toggle_key(prefix, "due_date"),
    )
    with st.form(f"{prefix}_form"):
        title = st.text_input("Action Title", key=f"{prefix}_title")
        due_date_value = st.date_input("Action Due Date", key=f"{prefix}_date", disabled=not due_enabled)
        details = st.text_area("Action Details", key=f"{prefix}_details")
        active_global = st.checkbox("Show in global Actions list now", key=f"{prefix}_active_global")
        submit = st.form_submit_button(submit_label)
    if submit:
        if not title.strip():
            st.error("Draft action title is required.")
        else:
            _append_draft_action(
                draft,
                {
                    "title": title.strip(),
                    "details": details.strip(),
                    "due_date": due_date_value.isoformat() if due_enabled else None,
                    "status": "Open",
                    "is_active_global": active_global,
                },
            )
            _reset_editor_state(prefix, editor_defaults)
            st.session_state[_toggle_key(prefix, "due_date")] = False
            st.success("Draft action added.")


def add_draft_delegation(draft: dict, *, prefix: str = "draft_delegation", submit_label: str = "Add Draft Delegation") -> None:
    editor_defaults = {
        "title": "",
        "details": "",
        "date": date.today(),
        "active_global": False,
    }
    _set_editor_defaults(prefix, editor_defaults)
    follow_up_enabled = st.checkbox(
        "Set follow-up date",
        value=bool(st.session_state.get(_toggle_key(prefix, "follow_up_date"), False)),
        key=_toggle_key(prefix, "follow_up_date"),
    )
    with st.form(f"{prefix}_form"):
        title = st.text_input("Delegation Title", key=f"{prefix}_title")
        follow_up_value = st.date_input("Follow-Up Date", key=f"{prefix}_date", disabled=not follow_up_enabled)
        details = st.text_area("Delegation Details", key=f"{prefix}_details")
        active_global = st.checkbox("Show in global Delegations list now", key=f"{prefix}_active_global")
        submit = st.form_submit_button(submit_label)
    if submit:
        if not title.strip():
            st.error("Draft delegation title is required.")
        else:
            _append_draft_delegation(
                draft,
                {
                    "title": title.strip(),
                    "details": details.strip(),
                    "follow_up_date": follow_up_value.isoformat() if follow_up_enabled else None,
                    "status": "Waiting",
                    "is_active_global": active_global,
                },
            )
            _reset_editor_state(prefix, editor_defaults)
            st.session_state[_toggle_key(prefix, "follow_up_date")] = False
            st.success("Draft delegation added.")


def create_project_linked_action(project: dict, *, prefix: str) -> None:
    data = st.session_state.data
    action_id = new_uuid()
    payload = {
        "id": action_id,
        "title": st.session_state.get(f"{prefix}_title", "").strip(),
        "details": st.session_state.get(f"{prefix}_details", "").strip(),
        "due_date": st.session_state.get(f"{prefix}_date").isoformat() if st.session_state.get(_toggle_key(prefix, "due_date")) else None,
        "status": "Open",
        "project_id": project["id"],
        "is_active_global": bool(st.session_state.get(f"{prefix}_active_global", False)),
    }
    data["actions"][action_id] = payload
    project.setdefault("action_ids", []).append(action_id)


def create_project_linked_delegation(project: dict, *, prefix: str) -> None:
    data = st.session_state.data
    delegation_id = new_uuid()
    payload = {
        "id": delegation_id,
        "title": st.session_state.get(f"{prefix}_title", "").strip(),
        "details": st.session_state.get(f"{prefix}_details", "").strip(),
        "follow_up_date": st.session_state.get(f"{prefix}_date").isoformat() if st.session_state.get(_toggle_key(prefix, "follow_up_date")) else None,
        "status": "Waiting",
        "project_id": project["id"],
        "is_active_global": bool(st.session_state.get(f"{prefix}_active_global", False)),
    }
    data["delegations"][delegation_id] = payload
    project.setdefault("delegation_ids", []).append(delegation_id)


def add_saved_project_action(project: dict) -> None:
    prefix = f"project_action_{project['id']}"
    editor_defaults = {
        "title": "",
        "details": "",
        "date": date.today(),
        "active_global": False,
    }
    _set_editor_defaults(prefix, editor_defaults)
    due_enabled = st.checkbox(
        "Set due date",
        value=bool(st.session_state.get(_toggle_key(prefix, "due_date"), False)),
        key=_toggle_key(prefix, "due_date"),
    )
    with st.form(f"{prefix}_form"):
        title = st.text_input("Action Title", key=f"{prefix}_title")
        st.date_input("Action Due Date", key=f"{prefix}_date", disabled=not due_enabled)
        st.text_area("Action Details", key=f"{prefix}_details")
        st.checkbox("Show in global Actions list now", key=f"{prefix}_active_global")
        submit = st.form_submit_button("Add Action")
    if submit:
        if not title.strip():
            st.error("Action title is required.")
        else:
            create_project_linked_action(project, prefix=prefix)
            _reset_editor_state(prefix, editor_defaults)
            st.session_state[_toggle_key(prefix, "due_date")] = False
            st.success("Action added to project.")


def add_saved_project_delegation(project: dict) -> None:
    prefix = f"project_delegation_{project['id']}"
    editor_defaults = {
        "title": "",
        "details": "",
        "date": date.today(),
        "active_global": False,
    }
    _set_editor_defaults(prefix, editor_defaults)
    follow_up_enabled = st.checkbox(
        "Set follow-up date",
        value=bool(st.session_state.get(_toggle_key(prefix, "follow_up_date"), False)),
        key=_toggle_key(prefix, "follow_up_date"),
    )
    with st.form(f"{prefix}_form"):
        title = st.text_input("Delegation Title", key=f"{prefix}_title")
        st.date_input("Follow-Up Date", key=f"{prefix}_date", disabled=not follow_up_enabled)
        st.text_area("Delegation Details", key=f"{prefix}_details")
        st.checkbox("Show in global Delegations list now", key=f"{prefix}_active_global")
        submit = st.form_submit_button("Add Delegation")
    if submit:
        if not title.strip():
            st.error("Delegation title is required.")
        else:
            create_project_linked_delegation(project, prefix=prefix)
            _reset_editor_state(prefix, editor_defaults)
            st.session_state[_toggle_key(prefix, "follow_up_date")] = False
            st.success("Delegation added to project.")


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

    draft_due_enabled = st.checkbox(
        "Set due date",
        value=bool(draft.get("due_date")),
        key="draft_project_due_enabled",
    )

    with st.form("draft_project_form"):
        title = st.text_input("Title", value=draft.get("title", ""))
        due_default = parse_date_only(draft.get("due_date")) or date.today()
        due_date_value = st.date_input("Due Date", value=due_default, disabled=not draft_due_enabled)
        description = st.text_area("Description", value=draft.get("description", ""), height=180)
        status = st.selectbox("Status", ["Active", "Someday"], index=0 if draft.get("status", "Active") == "Active" else 1)
        save = st.form_submit_button("Save")
        back = st.form_submit_button("Back")

    draft["title"] = title
    draft["description"] = description
    draft["status"] = status
    draft["due_date"] = due_date_value.isoformat() if draft_due_enabled else None

    st.markdown(f"**Linked items:** {draft_linked_count(draft)}")
    st.markdown("**Draft Actions**")
    render_task_rows(draft.get("draft_actions", []), "Draft Actions", date_field="due_date", date_label="Due")
    with st.expander("Add Draft Action"):
        add_draft_action(draft)
    st.markdown("**Draft Delegations**")
    render_task_rows(draft.get("draft_delegations", []), "Draft Delegations", date_field="follow_up_date", date_label="Follow-Up")
    with st.expander("Add Draft Delegation"):
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

    project_due_enabled = st.checkbox(
        "Set due date",
        value=bool(project.get("due_date")),
        key=f"project_due_enabled_{project_id}",
    )

    with st.form("project_detail_form"):
        title = st.text_input("Title", value=project.get("title", ""))
        due_default = parse_date_only(project.get("due_date")) or date.today()
        due_date_value = st.date_input("Due Date", value=due_default, disabled=not project_due_enabled)
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

    with st.expander("Add Action"):
        add_saved_project_action(project)
    with st.expander("Add Delegation"):
        add_saved_project_delegation(project)

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
            project["due_date"] = due_date_value.isoformat() if project_due_enabled else None
            project["status"] = status
            st.success("Project updated.")
