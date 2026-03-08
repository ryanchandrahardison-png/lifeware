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


def _ensure_widget_defaults(prefix: str, values: dict) -> None:
    for key, value in values.items():
        st.session_state.setdefault(f"{prefix}_{key}", value)


def _set_widget_values(prefix: str, values: dict) -> None:
    for key, value in values.items():
        st.session_state[f"{prefix}_{key}"] = value


def _queue_widget_values(prefix: str, values: dict) -> None:
    pending = st.session_state.setdefault("_project_item_pending_widget_values", {})
    pending[prefix] = dict(values)


def _apply_pending_widget_values(prefix: str) -> bool:
    pending = st.session_state.get("_project_item_pending_widget_values", {})
    values = pending.pop(prefix, None)
    if values is None:
        return False
    _set_widget_values(prefix, values)
    if not pending:
        st.session_state.pop("_project_item_pending_widget_values", None)
    return True


def _queue_notice(message: str) -> None:
    st.session_state["_project_item_notice"] = message


def _render_notice() -> None:
    message = st.session_state.pop("_project_item_notice", None)
    if message:
        st.success(message)


def _editor_text(prefix: str, name: str) -> str:
    return str(st.session_state.get(f"{prefix}_{name}", "")).strip()


def _editor_date_value(prefix: str, name: str) -> str | None:
    raw_value = st.session_state.get(f"{prefix}_{name}")
    if raw_value in (None, ""):
        return None
    if isinstance(raw_value, date):
        return raw_value.isoformat()
    parsed = parse_date_only(raw_value)
    return parsed.isoformat() if parsed else None


def _reset_action_editor(prefix: str) -> None:
    _set_widget_values(
        prefix,
        {
            "title": "",
            "details": "",
            "date": None,
            "active_global": False,
        },
    )


def _reset_delegation_editor(prefix: str) -> None:
    _set_widget_values(
        prefix,
        {
            "title": "",
            "details": "",
            "date": None,
            "active_global": False,
        },
    )


def _append_draft_action(draft: dict, item: dict) -> None:
    draft.setdefault("draft_actions", []).append(item)


def _append_draft_delegation(draft: dict, item: dict) -> None:
    draft.setdefault("draft_delegations", []).append(item)


def _sync_draft_from_widgets(draft: dict, prefix: str = "draft_project") -> None:
    draft["title"] = _editor_text(prefix, "title")
    draft["description"] = str(st.session_state.get(f"{prefix}_description", "")).strip()
    draft["status"] = st.session_state.get(f"{prefix}_status", "Active")
    draft["due_date"] = _editor_date_value(prefix, "due_date")


def _load_draft_into_widgets(draft: dict, prefix: str = "draft_project") -> None:
    _ensure_widget_defaults(
        prefix,
        {
            "title": draft.get("title", ""),
            "description": draft.get("description", ""),
            "status": draft.get("status", "Active"),
            "due_date": parse_date_only(draft.get("due_date")),
        },
    )


def _load_project_into_widgets(project: dict, prefix: str) -> None:
    snapshot = (
        project.get("title", ""),
        project.get("description", ""),
        project.get("due_date"),
        project.get("status", "Active"),
    )
    if st.session_state.get(f"{prefix}_snapshot") != snapshot:
        _set_widget_values(
            prefix,
            {
                "title": project.get("title", ""),
                "description": project.get("description", ""),
                "due_date": parse_date_only(project.get("due_date")),
                "status": project.get("status", "Active"),
            },
        )
        st.session_state[f"{prefix}_snapshot"] = snapshot


def add_draft_action(draft: dict, *, prefix: str = "draft_action") -> None:
    if not _apply_pending_widget_values(prefix):
        _ensure_widget_defaults(
            prefix,
            {
                "title": "",
                "details": "",
                "date": None,
                "active_global": False,
            },
        )
    st.text_input("Action Title", key=f"{prefix}_title")
    st.date_input("Action Due Date", key=f"{prefix}_date", value=None)
    st.text_area("Action Details", key=f"{prefix}_details")
    st.checkbox("Show in global Actions list now", key=f"{prefix}_active_global")
    if st.button("Add Draft Action", key=f"{prefix}_submit"):
        title = _editor_text(prefix, "title")
        if not title:
            st.error("Draft action title is required.")
        else:
            _append_draft_action(
                draft,
                {
                    "title": title,
                    "details": _editor_text(prefix, "details"),
                    "due_date": _editor_date_value(prefix, "date"),
                    "status": "Open",
                    "is_active_global": bool(st.session_state.get(f"{prefix}_active_global", False)),
                },
            )
            _queue_widget_values(
                prefix,
                {
                    "title": "",
                    "details": "",
                    "date": None,
                    "active_global": False,
                },
            )
            _queue_notice("Draft action added.")
            st.rerun()


def add_draft_delegation(draft: dict, *, prefix: str = "draft_delegation") -> None:
    if not _apply_pending_widget_values(prefix):
        _ensure_widget_defaults(
            prefix,
            {
                "title": "",
                "details": "",
                "date": None,
                "active_global": False,
            },
        )
    st.text_input("Delegation Title", key=f"{prefix}_title")
    st.date_input("Follow-Up Date", key=f"{prefix}_date", value=None)
    st.text_area("Delegation Details", key=f"{prefix}_details")
    st.checkbox("Show in global Delegations list now", key=f"{prefix}_active_global")
    if st.button("Add Draft Delegation", key=f"{prefix}_submit"):
        title = _editor_text(prefix, "title")
        if not title:
            st.error("Draft delegation title is required.")
        else:
            _append_draft_delegation(
                draft,
                {
                    "title": title,
                    "details": _editor_text(prefix, "details"),
                    "follow_up_date": _editor_date_value(prefix, "date"),
                    "status": "Waiting",
                    "is_active_global": bool(st.session_state.get(f"{prefix}_active_global", False)),
                },
            )
            _queue_widget_values(
                prefix,
                {
                    "title": "",
                    "details": "",
                    "date": None,
                    "active_global": False,
                },
            )
            _queue_notice("Draft delegation added.")
            st.rerun()


def create_project_linked_action(project: dict, *, prefix: str) -> None:
    data = st.session_state.data
    action_id = new_uuid()
    payload = {
        "id": action_id,
        "title": _editor_text(prefix, "title"),
        "details": _editor_text(prefix, "details"),
        "due_date": _editor_date_value(prefix, "date"),
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
        "title": _editor_text(prefix, "title"),
        "details": _editor_text(prefix, "details"),
        "follow_up_date": _editor_date_value(prefix, "date"),
        "status": "Waiting",
        "project_id": project["id"],
        "is_active_global": bool(st.session_state.get(f"{prefix}_active_global", False)),
    }
    data["delegations"][delegation_id] = payload
    project.setdefault("delegation_ids", []).append(delegation_id)


def add_saved_project_action(project: dict) -> None:
    prefix = f"project_action_{project['id']}"
    if not _apply_pending_widget_values(prefix):
        _ensure_widget_defaults(
            prefix,
            {
                "title": "",
                "details": "",
                "date": None,
                "active_global": False,
            },
        )
    st.text_input("Action Title", key=f"{prefix}_title")
    st.date_input("Action Due Date", key=f"{prefix}_date", value=None)
    st.text_area("Action Details", key=f"{prefix}_details")
    st.checkbox("Show in global Actions list now", key=f"{prefix}_active_global")
    if st.button("Add Action", key=f"{prefix}_submit"):
        if not _editor_text(prefix, "title"):
            st.error("Action title is required.")
        else:
            create_project_linked_action(project, prefix=prefix)
            _queue_widget_values(
                prefix,
                {
                    "title": "",
                    "details": "",
                    "date": None,
                    "active_global": False,
                },
            )
            _queue_notice("Action added to project.")
            st.rerun()


def add_saved_project_delegation(project: dict) -> None:
    prefix = f"project_delegation_{project['id']}"
    if not _apply_pending_widget_values(prefix):
        _ensure_widget_defaults(
            prefix,
            {
                "title": "",
                "details": "",
                "date": None,
                "active_global": False,
            },
        )
    st.text_input("Delegation Title", key=f"{prefix}_title")
    st.date_input("Follow-Up Date", key=f"{prefix}_date", value=None)
    st.text_area("Delegation Details", key=f"{prefix}_details")
    st.checkbox("Show in global Delegations list now", key=f"{prefix}_active_global")
    if st.button("Add Delegation", key=f"{prefix}_submit"):
        if not _editor_text(prefix, "title"):
            st.error("Delegation title is required.")
        else:
            create_project_linked_delegation(project, prefix=prefix)
            _queue_widget_values(
                prefix,
                {
                    "title": "",
                    "details": "",
                    "date": None,
                    "active_global": False,
                },
            )
            _queue_notice("Delegation added to project.")
            st.rerun()


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

_render_notice()

if not is_edit:
    draft = st.session_state.get("draft_project") or empty_draft()
    st.session_state.draft_project = draft
    _load_draft_into_widgets(draft)
    _sync_draft_from_widgets(draft)

    st.title("📁 Project Details")
    st.caption("Create a draft project and save it only when it has at least two linked items.")

    st.text_input("Title", key="draft_project_title")
    st.date_input("Due Date", key="draft_project_due_date", value=None)
    st.text_area("Description", key="draft_project_description", height=180)
    st.selectbox("Status", ["Active", "Someday"], key="draft_project_status")
    _sync_draft_from_widgets(draft)

    action_cols = st.columns(2)
    save = action_cols[0].button("Save")
    back = action_cols[1].button("Back")

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
    elif save:
        _sync_draft_from_widgets(draft)
        if save_draft_project(draft):
            st.switch_page("pages/projectItem.py")
else:
    project = data["projects"][project_id]
    prefix = f"project_edit_{project_id}"
    _load_project_into_widgets(project, prefix)

    linked_actions = linked_actions_for_project(data, project)
    linked_delegations = linked_delegations_for_project(data, project)
    can_complete = completion_ready(linked_actions, linked_delegations)
    st.title("📁 Project Details")
    st.caption(f"Health: {project_health(data, project)}")

    status_options = ["Active", "Someday", "Completed"]
    st.text_input("Title", key=f"{prefix}_title")
    st.date_input("Due Date", key=f"{prefix}_due_date", value=None)
    st.text_area("Description", key=f"{prefix}_description", height=180)
    st.selectbox("Status", status_options, key=f"{prefix}_status")

    if st.session_state.get(f"{prefix}_status") == "Completed" and not can_complete:
        st.caption("Complete Project is disabled until all linked actions and delegations are completed.")

    command_cols = st.columns(3)
    save = command_cols[0].button("Save")
    delete = command_cols[1].button("Delete")
    back = command_cols[2].button("Back")

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
                st.rerun()
            else:
                delete_project(project_id, choice)
        if confirm_cols[1].button("Back from Delete"):
            st.session_state.project_delete_mode = None
            st.rerun()

    if back:
        st.session_state.project_view_id = None
        st.session_state.project_delete_mode = None
        st.switch_page("pages/projects.py")
    elif delete:
        if project.get("action_ids") or project.get("delegation_ids"):
            st.session_state.project_delete_mode = project_id
            st.rerun()
        else:
            data["projects"].pop(project_id, None)
            st.session_state.project_view_id = None
            st.switch_page("pages/projects.py")
    elif save:
        status = st.session_state.get(f"{prefix}_status", "Active")
        if status == "Completed" and not can_complete:
            st.error("Project cannot be marked Completed until all linked actions and delegations are completed.")
        else:
            project["title"] = _editor_text(prefix, "title")
            project["description"] = str(st.session_state.get(f"{prefix}_description", "")).strip()
            project["due_date"] = _editor_date_value(prefix, "due_date")
            project["status"] = status
            st.session_state[f"{prefix}_snapshot"] = (
                project.get("title", ""),
                project.get("description", ""),
                project.get("due_date"),
                project.get("status", "Active"),
            )
            st.success("Project updated.")
