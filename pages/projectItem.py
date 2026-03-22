from __future__ import annotations

from copy import deepcopy
from datetime import date

import pandas as pd
import streamlit as st

from core.entities import (
    linked_actions_for_project,
    linked_delegations_for_project,
    parse_date_only,
    project_health,
)
from core.item_detail_form import delete_item_with_project_guard, save_item_with_constraints
from core.layout import sidebar_file_controls
from core.page_state import (
    clear_selection_keys,
    flags_store,
    pop_reset_flag,
    prepare_widget_defaults,
    reset_editor_namespace,
    sync_editor_from_widgets,
    ui_store,
    widget_key,
)
from core.project_linked_items import (
    count_grouped_items,
    filter_linked_items_by_activity,
    grouped_linked_items,
    linked_item_date,
    linked_item_date_text,
    linked_item_type,
    project_linked_items_with_unresolved,
)
from core.navigation import render_primary_navigation
from core.project_service import (
    DELETE_CHOICE_OPTIONS,
    create_linked_action,
    create_linked_delegation,
    delete_project,
    is_delete_cancellation_choice,
    request_project_delete,
    save_project_from_draft,
    remove_project_link_reference,
    validate_project_due_date_change,
    update_project_from_editor,
    validate_project_completion,
    validate_linked_item_date_change,
)
from core.state import init_state
from core.selection_utils import selected_single_row_index

st.set_page_config(page_title="Project Details", layout="wide")
init_state()
sidebar_file_controls()

render_primary_navigation()

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



def _clear_linked_item_modal_state() -> None:
    flags_store().pop("project_linked_item_modal", None)
    flags_store().pop("project_linked_item_modal_editor_key", None)


def _linked_item_table_key(scope: str, group: str) -> str:
    return f"project_linked_items::{scope}::{group}"


def _open_linked_item(item: dict) -> None:
    flags_store()["project_linked_item_modal"] = item
    flags_store().pop("project_linked_item_modal_editor_key", None)


@st.dialog("Linked Item Details")
def _linked_item_detail_dialog() -> None:
    modal_item = flags_store().get("project_linked_item_modal")
    if not isinstance(modal_item, dict):
        st.info("No linked item selected.")
        return

    kind = "delegation" if modal_item.get("kind") == "delegation" else "action"
    item_id = modal_item.get("id")
    collection_key = "delegations" if kind == "delegation" else "actions"
    date_field = "follow_up_date" if kind == "delegation" else "due_date"
    date_label = "Follow Up Date" if kind == "delegation" else "Due Date"
    status_options = ["Waiting", "Completed"] if kind == "delegation" else ["Open", "Completed"]

    if modal_item.get("unresolved"):
        st.warning("This linked item reference is unresolved and cannot be edited.")
        project_id = st.session_state.get("project_view_id")
        if project_id and item_id:
            remove_label = "Remove Broken Delegation Link" if kind == "delegation" else "Remove Broken Action Link"
            if st.button(remove_label, use_container_width=True):
                _remove_broken_project_link(
                    project_id=project_id,
                    item_type=kind,
                    item_id=item_id,
                )
                _clear_linked_item_modal_state()
                st.rerun()
        if st.button("Close", use_container_width=True):
            _clear_linked_item_modal_state()
            st.rerun()
        return

    record = None
    if item_id:
        record = deepcopy(st.session_state.data.get(collection_key, {}).get(item_id))

    if record is None:
        st.markdown(f"**Task Name:** {modal_item.get('title', 'Untitled')}")
        st.markdown(f"**Type:** {linked_item_type(modal_item)}")
        st.markdown(f"**Date:** {linked_item_date_text(modal_item)}")
        details_text = str(modal_item.get("details", "") or "").strip() or "(No details)"
        st.markdown("**Details**")
        st.write(details_text)
        st.caption("This linked item is not yet persisted; edit it from the draft controls.")
        if st.button("Close", use_container_width=True):
            _clear_linked_item_modal_state()
            st.rerun()
        return

    editor_key = f"project_linked_modal_editor::{kind}::{item_id}"
    title_key = f"{editor_key}::title"
    date_key = f"{editor_key}::date"
    details_key = f"{editor_key}::details"
    status_key = f"{editor_key}::status"

    if flags_store().get("project_linked_item_modal_editor_key") != editor_key:
        st.session_state[title_key] = str(record.get("title", "") or "")
        st.session_state[details_key] = str(record.get("details", "") or "")
        st.session_state[date_key] = parse_date_only(record.get(date_field)) or date.today()
        status_value = record.get("status", status_options[0])
        st.session_state[status_key] = status_value if status_value in status_options else status_options[0]
        flags_store()["project_linked_item_modal_editor_key"] = editor_key

    with st.form(f"project_linked_modal_form::{kind}::{item_id}"):
        st.text_input("Title", key=title_key)
        original_item_date = parse_date_only(record.get(date_field))
        current_item_date = parse_date_only(st.session_state.get(date_key))
        min_item_date = date.today()
        if original_item_date and original_item_date < date.today() and current_item_date == original_item_date:
            min_item_date = original_item_date
        st.date_input(date_label, key=date_key, min_value=min_item_date)
        st.text_area("Details", key=details_key, height=180)
        st.selectbox("Status", status_options, key=status_key)

        controls = st.columns(2)
        save = controls[0].form_submit_button("Save")
        delete = controls[1].form_submit_button("Delete")

    if delete:
        ok, errors = delete_item_with_project_guard(
            data=st.session_state.data,
            list_key=collection_key,
            item_id=item_id,
        )
        if not ok:
            for error in errors:
                st.error(error)
            return

        _clear_linked_item_modal_state()
        _queue_notice("Linked item deleted.")
        st.rerun()
        return

    if save:
        title = str(st.session_state.get(title_key, "") or "")
        selected_date = parse_date_only(st.session_state.get(date_key)) or date.today()
        details = str(st.session_state.get(details_key, "") or "")
        status = str(st.session_state.get(status_key, status_options[0]) or status_options[0])
        original_item_date = parse_date_only(record.get(date_field))
        date_check = validate_linked_item_date_change(
            selected_date=selected_date,
            original_date=original_item_date,
            date_label=date_label,
        )
        if not date_check.ok:
            for error in date_check.errors or []:
                st.error(error)
            return

        ok, errors, updated = save_item_with_constraints(
            data=st.session_state.data,
            list_key=collection_key,
            item_id=item_id,
            title=title,
            details=details,
            status=status,
            date_value=selected_date,
            date_field_candidates=[date_field],
        )
        if not ok:
            for error in errors:
                st.error(error)
            return

        _clear_linked_item_modal_state()
        _queue_notice("Linked item updated.")
        st.rerun()


def _remove_draft_linked_item(*, draft: dict, item: dict) -> None:
    if item.get("kind") == "delegation":
        draft["draft_delegations"] = [row for row in draft.get("draft_delegations", []) if row is not item]
        _queue_notice("Draft delegation removed.")
    else:
        draft["draft_actions"] = [row for row in draft.get("draft_actions", []) if row is not item]
        _queue_notice("Draft action removed.")
    _sync_draft_runtime(draft)


def _remove_broken_project_link(*, project_id: str, item_type: str, item_id: str) -> None:
    result = remove_project_link_reference(
        data=st.session_state.data,
        project_id=project_id,
        item_type=item_type,
        item_id=item_id,
    )
    if result.ok:
        _queue_notice(result.message or "Broken link removed.")
    else:
        for error in result.errors or []:
            st.error(error)


def _render_unresolved_warning(*, item: dict, warning: str, remove_label: str, on_remove) -> None:
    kind = linked_item_type(item)
    name = item.get("title") or "Untitled"
    st.warning(f"{warning} ({kind}: {name})")
    if st.button(remove_label, key=f"remove_unresolved::{item.get('kind')}::{item.get('id') or id(item)}"):
        on_remove()
        st.rerun()


def _render_linked_items(
    grouped_items: dict[str, list[dict]],
    *,
    draft: dict | None = None,
    project_id: str | None = None,
    show_controls: bool = True,
) -> None:
    compact_key = f"project_linked_items_compact::{project_id or 'draft'}"
    if compact_key not in st.session_state:
        ua = ""
        try:
            headers = getattr(st.context, "headers", None)
            if headers:
                ua = str(headers.get("user-agent", "") or "").lower()
        except Exception:
            ua = ""
        st.session_state[compact_key] = any(token in ua for token in ["iphone", "android", "mobile", "ipad"])

    if show_controls:
        st.markdown(
            """
            <style>
            .linked-section-note { margin-bottom: .4rem; opacity: .8; }
            </style>
            """,
            unsafe_allow_html=True,
        )
        st.markdown('<div class="linked-section-note">Select a row to open linked-item details.</div>', unsafe_allow_html=True)
        st.toggle("Compact linked-item view", key=compact_key, help="Use compact stacked rows (recommended for narrow screens).")
    use_compact_view = bool(st.session_state.get(compact_key, False))

    for group in ["Completed", "Past Due", "Upcoming", "Floating"]:
        items = grouped_items.get(group, [])
        st.markdown(f"**{group}**")
        if not items:
            st.caption("No linked items.")
            continue

        if use_compact_view:
            for idx, item in enumerate(items):
                task_name = item.get("title", "Untitled")
                task_type = linked_item_type(item)
                task_date = linked_item_date_text(item)
                row_label = f"{task_name}  |  {task_type}  |  {task_date}"
                if st.button(row_label, key=f"project_linked_compact::{project_id or 'draft'}::{group}::{idx}", use_container_width=True):
                    selected_id = item.get("id")
                    if not selected_id and draft is not None:
                        _render_unresolved_warning(
                            item=item,
                            warning="This linked item is still a draft and cannot be opened until the project is saved.",
                            remove_label="Remove Draft Linked Item",
                            on_remove=lambda item=item: _remove_draft_linked_item(draft=draft, item=item),
                        )
                    else:
                        _open_linked_item(item)
            continue

        rows = [
            {
                "Task Name": item.get("title", "Untitled"),
                "Type": linked_item_type(item),
                "Date": linked_item_date_text(item),
            }
            for item in items
        ]
        table_scope = project_id or "draft"
        table_key = _linked_item_table_key(table_scope, group)
        selection = st.dataframe(
            pd.DataFrame(rows),
            use_container_width=True,
            hide_index=True,
            on_select="rerun",
            selection_mode="single-row",
            key=table_key,
        )
        if flags_store().get("suppress_linked_item_selection_once"):
            continue
        selected_index, had_stale_selection = selected_single_row_index(selection, len(items))
        if had_stale_selection:
            st.session_state.pop(table_key, None)
            continue
        if selected_index is not None:
            selected_item = items[selected_index]
            selected_id = selected_item.get("id")
            if not selected_id and draft is not None:
                _render_unresolved_warning(
                    item=selected_item,
                    warning="This linked item is still a draft and cannot be opened until the project is saved.",
                    remove_label="Remove Draft Linked Item",
                    on_remove=lambda item=selected_item: _remove_draft_linked_item(draft=draft, item=item),
                )
            else:
                _open_linked_item(selected_item)

    if flags_store().pop("suppress_linked_item_selection_once", False):
        pass

def _queue_notice(message: str) -> None:
    flags_store()["project_item_notice"] = message


def _render_notice() -> None:
    message = flags_store().pop("project_item_notice", None)
    if message:
        st.success(message)


def _get_editor(namespace: str, defaults: dict) -> dict:
    editor = ui_store().get(namespace)
    if not isinstance(editor, dict):
        editor = deepcopy(defaults)
        ui_store()[namespace] = editor
    return editor


def _coerce_widget_value(field: str, value):
    if field.endswith("date") or field in {"date", "due_date", "follow_up_date"}:
        return parse_date_only(value)
    return value


def _prepare_project_widget_defaults(namespace: str, fields: list[str], editor: dict, *, force: bool = False) -> None:
    coerced = {field: _coerce_widget_value(field, editor.get(field)) for field in fields}
    prepare_widget_defaults(namespace, fields, coerced, force=force)


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


def _set_delete_mode(project_id: str | None) -> None:
    flags_store()["project_delete_mode"] = project_id
    st.session_state.project_delete_mode = project_id


def _get_delete_mode() -> str | None:
    flags = flags_store()
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
    editor = ui_store().get(DRAFT_PROJECT_NS)
    if not isinstance(editor, dict):
        source = st.session_state.get("draft_project") or empty_draft()
        editor = deepcopy(source)
        editor.setdefault("draft_actions", [])
        editor.setdefault("draft_delegations", [])
        ui_store()[DRAFT_PROJECT_NS] = editor
        st.session_state.draft_project = deepcopy(editor)
    return editor


def _sync_draft_runtime(draft: dict) -> None:
    st.session_state.draft_project = deepcopy(draft)


def _clear_draft_runtime() -> None:
    ui_store().pop(DRAFT_PROJECT_NS, None)
    ui_store().pop("draft_action_editor", None)
    ui_store().pop("draft_delegation_editor", None)
    flags_store().pop("reset::draft_action_editor", None)
    flags_store().pop("reset::draft_delegation_editor", None)
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
        or bool(flags_store().pop("reload_project_editor", False))
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
        _clear_linked_item_modal_state()
        clear_selection_keys("project_linked_items::")
        flags_store()["suppress_linked_item_selection_once"] = True
        flags_store()[f"reset::{PROJECT_EDITOR_NS}"] = True
    return editor


def _render_project_editor(namespace: str, editor: dict, *, status_options: list[str], original_due_date: date | None = None) -> None:
    _prepare_project_widget_defaults(namespace, PROJECT_FIELDS, editor, force=pop_reset_flag(namespace))
    st.text_input("Title", key=widget_key(namespace, "title"))
    today = date.today()
    current_due = parse_date_only(editor.get("due_date"))
    min_due = today
    if original_due_date and original_due_date < today and current_due == original_due_date:
        min_due = original_due_date
    st.date_input("Due Date", key=widget_key(namespace, "due_date"), value=None, min_value=min_due)
    st.text_area("Description", key=widget_key(namespace, "description"), height=180)
    st.selectbox("Status", status_options, key=widget_key(namespace, "status"))
    sync_editor_from_widgets(namespace, PROJECT_FIELDS, editor)


def _render_action_editor(namespace: str, button_label: str) -> tuple[dict, bool]:
    editor = _get_editor(namespace, ACTION_EDITOR_DEFAULTS)
    _prepare_project_widget_defaults(namespace, ACTION_EDITOR_FIELDS, editor, force=pop_reset_flag(namespace))
    st.text_input("Action Title", key=widget_key(namespace, "title"))
    st.date_input("Action Due Date", key=widget_key(namespace, "date"), value=None, min_value=date.today())
    st.text_area("Action Details", key=widget_key(namespace, "details"))
    st.checkbox("Show in global Actions list now", key=widget_key(namespace, "active_global"))
    sync_editor_from_widgets(namespace, ACTION_EDITOR_FIELDS, editor)
    return editor, st.button(button_label, key=f"{namespace}__submit")


def _render_delegation_editor(namespace: str, button_label: str) -> tuple[dict, bool]:
    editor = _get_editor(namespace, DELEGATION_EDITOR_DEFAULTS)
    _prepare_project_widget_defaults(namespace, DELEGATION_EDITOR_FIELDS, editor, force=pop_reset_flag(namespace))
    st.text_input("Delegation Title", key=widget_key(namespace, "title"))
    st.date_input("Follow-Up Date", key=widget_key(namespace, "date"), value=None)
    st.text_area("Delegation Details", key=widget_key(namespace, "details"))
    st.checkbox("Show in global Delegations list now", key=widget_key(namespace, "active_global"))
    sync_editor_from_widgets(namespace, DELEGATION_EDITOR_FIELDS, editor)
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
        reset_editor_namespace(namespace, ACTION_EDITOR_DEFAULTS)
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
        reset_editor_namespace(namespace, DELEGATION_EDITOR_DEFAULTS)
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
        reset_editor_namespace(namespace, ACTION_EDITOR_DEFAULTS)
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
        reset_editor_namespace(namespace, DELEGATION_EDITOR_DEFAULTS)
        _queue_notice("Delegation added to project.")
        st.rerun()


@st.dialog("Add Task")
def _saved_action_dialog(project: dict) -> None:
    add_saved_project_action(project)


@st.dialog("Add Delegation")
def _saved_delegation_dialog(project: dict) -> None:
    add_saved_project_delegation(project)


@st.dialog("Add Draft Action")
def _draft_action_dialog(draft: dict) -> None:
    add_draft_action(draft)


@st.dialog("Add Draft Delegation")
def _draft_delegation_dialog(draft: dict) -> None:
    add_draft_delegation(draft)


project_id = st.session_state.project_view_id
data = st.session_state.data
is_edit = project_id is not None and project_id in data.get("projects", {})

_render_notice()

if not is_edit:
    draft = _draft_project_ui()

    st.title("📁 Project Details")
    st.caption("Create a draft project and save it only when it has at least two linked items.")

    _render_project_editor(DRAFT_PROJECT_NS, draft, status_options=["Active", "Someday"])
    draft["due_date"] = _editor_date_value(draft, "due_date")
    _sync_draft_runtime(draft)

    st.markdown(f"**Linked items:** {draft_linked_count(draft)}")
    draft_grouped_items = grouped_linked_items(
        draft.get("draft_actions", []),
        draft.get("draft_delegations", []),
    )
    st.markdown("**Linked Items**")
    _render_linked_items(draft_grouped_items, draft=draft)

    add_cols = st.columns(2)
    if add_cols[0].button("Add Action", use_container_width=True):
        reset_editor_namespace("draft_action_editor", ACTION_EDITOR_DEFAULTS)
        _draft_action_dialog(draft)
    if add_cols[1].button("Add Delegation", use_container_width=True):
        reset_editor_namespace("draft_delegation_editor", DELEGATION_EDITOR_DEFAULTS)
        _draft_delegation_dialog(draft)

    action_cols = st.columns(2)
    save = action_cols[0].button("Save", use_container_width=True)
    back = action_cols[1].button("Back", use_container_width=True)

    if back:
        _clear_draft_runtime()
        st.switch_page("pages/projects.py")
    elif save:
        result = save_project_from_draft(data=st.session_state.data, draft=draft)
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
        status="Completed",
        linked_actions=linked_actions,
        linked_delegations=linked_delegations,
    )
    can_complete = completion_check.ok

    st.title("📁 Project Details")
    st.caption(f"Health: {project_health(data, project)}")

    project_status_options = ["Active", "Someday", "Completed"] if (can_complete or project.get("status") == "Completed") else ["Active", "Someday"]
    _render_project_editor(
        PROJECT_EDITOR_NS,
        editor,
        status_options=project_status_options,
        original_due_date=parse_date_only(project.get("due_date")),
    )

    if editor.get("status") == "Completed" and not can_complete:
        st.caption("Complete Project is disabled until all linked actions and delegations are completed.")

    nav_cols = st.columns(3)
    save = False
    delete = False
    back = nav_cols[2].button("Back", use_container_width=True)

    linked_actions_with_unresolved, linked_delegations_with_unresolved = project_linked_items_with_unresolved(data, project)
    grouped_items = grouped_linked_items(linked_actions_with_unresolved, linked_delegations_with_unresolved)
    next_actions_grouped = filter_linked_items_by_activity(grouped_items, active=True)
    backlog_grouped = filter_linked_items_by_activity(grouped_items, active=False)

    st.markdown("**Next Actions**")
    if count_grouped_items(next_actions_grouped) == 0:
        st.caption("No next actions.")
    else:
        _render_linked_items(next_actions_grouped, project_id=f"{project_id}::next", show_controls=True)

    st.markdown("**Backlog Tasks**")
    if count_grouped_items(backlog_grouped) == 0:
        st.caption("No backlog tasks.")
    else:
        _render_linked_items(backlog_grouped, project_id=f"{project_id}::backlog", show_controls=False)

    add_cols = st.columns(2)
    open_add_task_dialog = add_cols[0].button("Add Task", use_container_width=True)
    open_add_delegation_dialog = add_cols[1].button("Add Delegation", use_container_width=True)
    if open_add_task_dialog:
        _clear_linked_item_modal_state()
        reset_editor_namespace(f"project_action_editor::{project['id']}", ACTION_EDITOR_DEFAULTS)
    if open_add_delegation_dialog:
        _clear_linked_item_modal_state()
        reset_editor_namespace(f"project_delegation_editor::{project['id']}", DELEGATION_EDITOR_DEFAULTS)

    action_cols = st.columns(2)
    save = action_cols[0].button("Save", use_container_width=True)
    delete = action_cols[1].button("Delete", use_container_width=True)

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
            if is_delete_cancellation_choice(choice):
                _set_delete_mode(None)
                st.rerun()
            else:
                result = delete_project(data=data, project_id=project_id, choice=choice)
                if result.deleted:
                    st.session_state.project_view_id = None
                    _set_delete_mode(None)
                    ui_store().pop(PROJECT_EDITOR_NS, None)
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
        ui_store().pop(PROJECT_EDITOR_NS, None)
        st.switch_page("pages/projects.py")
    elif delete:
        delete_request = request_project_delete(data=data, project_id=project_id)
        if not delete_request.ok:
            for error in delete_request.errors or []:
                st.error(error)
        elif delete_request.requires_choice:
            _set_delete_mode(project_id)
            st.rerun()
        elif delete_request.deleted:
            st.session_state.project_view_id = None
            _set_delete_mode(None)
            ui_store().pop(PROJECT_EDITOR_NS, None)
            st.switch_page("pages/projects.py")
    elif save:
        status = editor.get("status", "Active")
        selected_due_date = parse_date_only(editor.get("due_date"))
        original_due_date = parse_date_only(project.get("due_date"))
        due_date_check = validate_project_due_date_change(
            selected_due_date=selected_due_date,
            original_due_date=original_due_date,
        )
        if not due_date_check.ok:
            for error in due_date_check.errors or []:
                st.error(error)
        else:
            result = update_project_from_editor(
                data=data,
                project_id=project_id,
                title=_editor_text(editor, "title"),
                description=_editor_text(editor, "description"),
                due_date=_editor_date_value(editor, "due_date"),
                status=status,
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

    if open_add_task_dialog:
        _saved_action_dialog(project)
    elif open_add_delegation_dialog:
        _saved_delegation_dialog(project)
    elif flags_store().get("project_linked_item_modal"):
        _linked_item_detail_dialog()
