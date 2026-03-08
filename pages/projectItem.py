from __future__ import annotations

from copy import deepcopy
from datetime import date

import streamlit as st

from core.entities import (
    action_is_active,
    delegation_is_active,
    linked_actions_for_project,
    linked_delegations_for_project,
    parse_date_only,
    project_health,
)
from core.layout import sidebar_file_controls
from core.project_service import (
    DELETE_CHOICE_OPTIONS,
    create_linked_action,
    create_linked_delegation,
    delete_project,
    save_new_project,
    update_project,
    validate_project_completion,
)
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

st.session_state.setdefault("ui", {})
st.session_state.setdefault("flags", {})

PROJECT_EDITOR_NS = "project_editor"
DRAFT_PROJECT_NS = "draft_project"

def empty_draft() -> dict:
    return {
        "title": "",
        "description": "",
        "due_date": None,
        "status": "Active",
        "draft_actions": [],
        "draft_delegations": [],
    }



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


def _ui_store() -> dict:
    return st.session_state.ui


def _flags_store() -> dict:
    return st.session_state.flags


def _widget_key(namespace: str, field: str) -> str:
    return f"{namespace}__{field}"


def _queue_notice(message: str) -> None:
    _flags_store()["project_item_notice"] = message


def _render_notice() -> None:
    message = _flags_store().pop("project_item_notice", None)
    if message:
        st.success(message)


def _get_editor(namespace: str, defaults: dict) -> dict:
    editor = _ui_store().get(namespace)
    if not isinstance(editor, dict):
        editor = deepcopy(defaults)
        _ui_store()[namespace] = editor
    return editor


def _coerce_widget_value(field: str, value):
    if field.endswith("date") or field in {"date", "due_date", "follow_up_date"}:
        return parse_date_only(value)
    return value


def _prepare_widget_defaults(namespace: str, fields: list[str], editor: dict, *, force: bool = False) -> None:
    for field in fields:
        key = _widget_key(namespace, field)
        if force or key not in st.session_state:
            st.session_state[key] = _coerce_widget_value(field, editor.get(field))


def _sync_editor_from_widgets(namespace: str, fields: list[str], editor: dict) -> None:
    for field in fields:
        editor[field] = st.session_state.get(_widget_key(namespace, field))


def _editor_text(editor: dict, field: str) -> str:
    return str(editor.get(field, "") or "").strip()


def _editor_date_value(editor: dict, field: str) -> str | None:
    raw_value = editor.get(field)
    if raw_value in (None, ""):
        return None
    if isinstance(raw_value, date):
        return raw_value.isoformat()
    parsed = parse_date_only(raw_value)
    return parsed.isoformat() if parsed else None


def _reset_editor(namespace: str, defaults: dict) -> None:
    _ui_store()[namespace] = deepcopy(defaults)
    _flags_store()[f"reset::{namespace}"] = True


def _pop_reset_flag(namespace: str) -> bool:
    return bool(_flags_store().pop(f"reset::{namespace}", False))


def _set_delete_mode(project_id: str | None) -> None:
    _flags_store()["project_delete_mode"] = project_id
    st.session_state.project_delete_mode = project_id


def _get_delete_mode() -> str | None:
    flags = _flags_store()
    if "project_delete_mode" not in flags:
        flags["project_delete_mode"] = st.session_state.get("project_delete_mode")
    return flags.get("project_delete_mode")


def _append_draft_action(draft: dict, item: dict) -> None:
    draft.setdefault("draft_actions", []).append(item)


def _append_draft_delegation(draft: dict, item: dict) -> None:
    draft.setdefault("draft_delegations", []).append(item)


PROJECT_DEFAULTS = {
    "title": "",
    "description": "",
    "due_date": None,
    "status": "Active",
}
ACTION_EDITOR_DEFAULTS = {
    "title": "",
    "details": "",
    "date": None,
    "active_global": False,
}
DELEGATION_EDITOR_DEFAULTS = {
    "title": "",
    "details": "",
    "date": None,
    "active_global": False,
}
PROJECT_FIELDS = ["title", "description", "due_date", "status"]
ACTION_EDITOR_FIELDS = ["title", "details", "date", "active_global"]
DELEGATION_EDITOR_FIELDS = ["title", "details", "date", "active_global"]


def _draft_project_ui() -> dict:
    editor = _ui_store().get(DRAFT_PROJECT_NS)
    if not isinstance(editor, dict):
        source = st.session_state.get("draft_project") or empty_draft()
        editor = deepcopy(source)
        editor.setdefault("draft_actions", [])
        editor.setdefault("draft_delegations", [])
        _ui_store()[DRAFT_PROJECT_NS] = editor
        st.session_state.draft_project = deepcopy(editor)
    return editor


def _sync_draft_runtime(draft: dict) -> None:
    st.session_state.draft_project = deepcopy(draft)


def _clear_draft_runtime() -> None:
    _ui_store().pop(DRAFT_PROJECT_NS, None)
    _ui_store().pop("draft_action_editor", None)
    _ui_store().pop("draft_delegation_editor", None)
    _flags_store().pop("reset::draft_action_editor", None)
    _flags_store().pop("reset::draft_delegation_editor", None)
    st.session_state.draft_project = None


def _load_project_editor(project: dict) -> dict:
    editor = _get_editor(PROJECT_EDITOR_NS, PROJECT_DEFAULTS)
    snapshot = (
        project.get("title", ""),
        project.get("description", ""),
        project.get("due_date"),
        project.get("status", "Active"),
    )
    if (
        editor.get("loaded_project_id") != project.get("id")
        or editor.get("source_snapshot") != snapshot
        or bool(_flags_store().pop("reload_project_editor", False))
    ):
        editor.update(
            {
                "title": project.get("title", ""),
                "description": project.get("description", ""),
                "due_date": parse_date_only(project.get("due_date")),
                "status": project.get("status", "Active"),
                "loaded_project_id": project.get("id"),
                "source_snapshot": snapshot,
            }
        )
        _flags_store()[f"reset::{PROJECT_EDITOR_NS}"] = True
    return editor


def _render_project_editor(namespace: str, editor: dict, *, status_options: list[str]) -> None:
    _prepare_widget_defaults(namespace, PROJECT_FIELDS, editor, force=_pop_reset_flag(namespace))
    st.text_input("Title", key=_widget_key(namespace, "title"))
    st.date_input("Due Date", key=_widget_key(namespace, "due_date"), value=None)
    st.text_area("Description", key=_widget_key(namespace, "description"), height=180)
    st.selectbox("Status", status_options, key=_widget_key(namespace, "status"))
    _sync_editor_from_widgets(namespace, PROJECT_FIELDS, editor)


def _render_action_editor(namespace: str, button_label: str) -> tuple[dict, bool]:
    editor = _get_editor(namespace, ACTION_EDITOR_DEFAULTS)
    _prepare_widget_defaults(namespace, ACTION_EDITOR_FIELDS, editor, force=_pop_reset_flag(namespace))
    st.text_input("Action Title", key=_widget_key(namespace, "title"))
    st.date_input("Action Due Date", key=_widget_key(namespace, "date"), value=None)
    st.text_area("Action Details", key=_widget_key(namespace, "details"))
    st.checkbox("Show in global Actions list now", key=_widget_key(namespace, "active_global"))
    _sync_editor_from_widgets(namespace, ACTION_EDITOR_FIELDS, editor)
    return editor, st.button(button_label, key=f"{namespace}__submit")


def _render_delegation_editor(namespace: str, button_label: str) -> tuple[dict, bool]:
    editor = _get_editor(namespace, DELEGATION_EDITOR_DEFAULTS)
    _prepare_widget_defaults(namespace, DELEGATION_EDITOR_FIELDS, editor, force=_pop_reset_flag(namespace))
    st.text_input("Delegation Title", key=_widget_key(namespace, "title"))
    st.date_input("Follow-Up Date", key=_widget_key(namespace, "date"), value=None)
    st.text_area("Delegation Details", key=_widget_key(namespace, "details"))
    st.checkbox("Show in global Delegations list now", key=_widget_key(namespace, "active_global"))
    _sync_editor_from_widgets(namespace, DELEGATION_EDITOR_FIELDS, editor)
    return editor, st.button(button_label, key=f"{namespace}__submit")


def add_draft_action(draft: dict) -> None:
    namespace = "draft_action_editor"
    editor, submitted = _render_action_editor(namespace, "Add Draft Action")
    if submitted:
        title = _editor_text(editor, "title")
        if not title:
            st.error("Draft action title is required.")
            return
        _append_draft_action(
            draft,
            {
                "title": title,
                "details": _editor_text(editor, "details"),
                "due_date": _editor_date_value(editor, "date"),
                "status": "Open",
                "is_active_global": bool(editor.get("active_global", False)),
            },
        )
        _sync_draft_runtime(draft)
        _reset_editor(namespace, ACTION_EDITOR_DEFAULTS)
        _queue_notice("Draft action added.")
        st.rerun()


def add_draft_delegation(draft: dict) -> None:
    namespace = "draft_delegation_editor"
    editor, submitted = _render_delegation_editor(namespace, "Add Draft Delegation")
    if submitted:
        title = _editor_text(editor, "title")
        if not title:
            st.error("Draft delegation title is required.")
            return
        _append_draft_delegation(
            draft,
            {
                "title": title,
                "details": _editor_text(editor, "details"),
                "follow_up_date": _editor_date_value(editor, "date"),
                "status": "Waiting",
                "is_active_global": bool(editor.get("active_global", False)),
            },
        )
        _sync_draft_runtime(draft)
        _reset_editor(namespace, DELEGATION_EDITOR_DEFAULTS)
        _queue_notice("Draft delegation added.")
        st.rerun()




def add_saved_project_action(project: dict) -> None:
    namespace = f"project_action_editor::{project['id']}"
    editor, submitted = _render_action_editor(namespace, "Add Action")
    if submitted:
        if not _editor_text(editor, "title"):
            st.error("Action title is required.")
            return
        create_linked_action(
            data=st.session_state.data,
            project_id=project["id"],
            title=_editor_text(editor, "title"),
            details=_editor_text(editor, "details"),
            due_date=_editor_date_value(editor, "date"),
            is_active_global=bool(editor.get("active_global", False)),
        )
        _reset_editor(namespace, ACTION_EDITOR_DEFAULTS)
        _queue_notice("Action added to project.")
        st.rerun()


def add_saved_project_delegation(project: dict) -> None:
    namespace = f"project_delegation_editor::{project['id']}"
    editor, submitted = _render_delegation_editor(namespace, "Add Delegation")
    if submitted:
        if not _editor_text(editor, "title"):
            st.error("Delegation title is required.")
            return
        create_linked_delegation(
            data=st.session_state.data,
            project_id=project["id"],
            title=_editor_text(editor, "title"),
            details=_editor_text(editor, "details"),
            follow_up_date=_editor_date_value(editor, "date"),
            is_active_global=bool(editor.get("active_global", False)),
        )
        _reset_editor(namespace, DELEGATION_EDITOR_DEFAULTS)
        _queue_notice("Delegation added to project.")
        st.rerun()


project_id = st.session_state.project_view_id
data = st.session_state.data
is_edit = project_id is not None and project_id in data.get("projects", {})

_render_notice()

if not is_edit:
    draft = _draft_project_ui()
    _render_project_editor(DRAFT_PROJECT_NS, draft, status_options=["Active", "Someday"])
    draft["due_date"] = _editor_date_value(draft, "due_date")
    _sync_draft_runtime(draft)

    st.title("📁 Project Details")
    st.caption("Create a draft project and save it only when it has at least two linked items.")

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
        _clear_draft_runtime()
        st.switch_page("pages/projects.py")
    elif save:
        result = save_new_project(data=st.session_state.data, draft=draft)
        if not result.ok:
            for error in result.errors or []:
                st.error(error)
        else:
            st.session_state.project_view_id = result.project_id
            _clear_draft_runtime()
            _queue_notice(result.message or "Project saved.")
            st.switch_page("pages/projectItem.py")
else:
    project = data["projects"][project_id]
    editor = _load_project_editor(project)

    linked_actions = linked_actions_for_project(data, project)
    linked_delegations = linked_delegations_for_project(data, project)
    completion_check = validate_project_completion(
        status=editor.get("status", project.get("status", "Active")),
        linked_actions=linked_actions,
        linked_delegations=linked_delegations,
    )
    can_complete = completion_check.ok

    st.title("📁 Project Details")
    st.caption(f"Health: {project_health(data, project)}")

    _render_project_editor(PROJECT_EDITOR_NS, editor, status_options=["Active", "Someday", "Completed"])

    if editor.get("status") == "Completed" and not can_complete:
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

    if _get_delete_mode() == project_id:
        st.warning("This project has linked items. Choose how deletion should be handled.")
        st.radio(
            "Deletion behavior",
            DELETE_CHOICE_OPTIONS,
            key="project_delete_choice",
        )
        confirm_cols = st.columns(2)
        if confirm_cols[0].button("Confirm Project Delete"):
            choice = st.session_state.get("project_delete_choice", DELETE_CHOICE_OPTIONS[0])
            if choice == "Cancel deletion":
                _set_delete_mode(None)
                st.rerun()
            else:
                result = delete_project(data=data, project_id=project_id, choice=choice)
                if result.deleted:
                    st.session_state.project_view_id = None
                    _set_delete_mode(None)
                    _ui_store().pop(PROJECT_EDITOR_NS, None)
                    st.switch_page("pages/projects.py")
                elif not result.ok:
                    for error in result.errors or []:
                        st.error(error)
                else:
                    _set_delete_mode(None)
                    st.rerun()
        if confirm_cols[1].button("Back from Delete"):
            _set_delete_mode(None)
            st.rerun()

    if back:
        st.session_state.project_view_id = None
        _set_delete_mode(None)
        _ui_store().pop(PROJECT_EDITOR_NS, None)
        st.switch_page("pages/projects.py")
    elif delete:
        if project.get("action_ids") or project.get("delegation_ids"):
            _set_delete_mode(project_id)
            st.rerun()
        else:
            result = delete_project(data=data, project_id=project_id, choice=DELETE_CHOICE_DELETE)
            if result.deleted:
                st.session_state.project_view_id = None
                _set_delete_mode(None)
                _ui_store().pop(PROJECT_EDITOR_NS, None)
                st.switch_page("pages/projects.py")
    elif save:
        status = editor.get("status", "Active")
        result = update_project(
            project=project,
            title=_editor_text(editor, "title"),
            description=_editor_text(editor, "description"),
            due_date=_editor_date_value(editor, "due_date"),
            status=status,
            linked_actions=linked_actions,
            linked_delegations=linked_delegations,
        )
        if not result.ok:
            for error in result.errors or []:
                st.error(error)
        else:
            editor["source_snapshot"] = (
                project.get("title", ""),
                project.get("description", ""),
                project.get("due_date"),
                project.get("status", "Active"),
            )
            editor["loaded_project_id"] = project_id
            st.success(result.message or "Project updated.")
