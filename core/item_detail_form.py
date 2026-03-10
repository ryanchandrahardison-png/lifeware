from __future__ import annotations

from copy import deepcopy
from datetime import date
from typing import Any

import streamlit as st

from core.entities import new_uuid
from core.project_service import validate_project_save

DEFAULT_STATUS_OPTIONS = ["Open", "Completed"]
DELEGATION_STATUS_OPTIONS = ["Waiting", "Completed"]
DATE_FIELD_CANDIDATES = ["due_date"]
FOLLOW_UP_FIELD_CANDIDATES = ["follow_up_date"]
SOURCE_FIELD_NAMES = {"source"}


def _as_dict(item: Any) -> dict:
    return deepcopy(item) if isinstance(item, dict) else {"title": "" if item is None else str(item)}


def _pick(record: dict, keys: list[str], default: str = "") -> str:
    for key in keys:
        value = record.get(key)
        if value not in (None, ""):
            return str(value)
    return default


def _parse_iso_date(value: Any) -> date | None:
    if value in (None, ""):
        return None
    if isinstance(value, date):
        return value
    try:
        text = str(value).strip()
        if "T" in text:
            text = text.split("T", 1)[0]
        return date.fromisoformat(text)
    except Exception:
        return None


def _status_index(status: str, options: list[str]) -> int:
    if status in options:
        return options.index(status)
    lowered = status.lower()
    for i, option in enumerate(options):
        if option.lower() == lowered:
            return i
    return 0


def _delete_known_date_keys(record: dict, field_candidates: list[str]) -> None:
    for key in field_candidates:
        record.pop(key, None)


def _sanitize_source_keys(record: dict) -> dict:
    return {k: v for k, v in record.items() if k not in SOURCE_FIELD_NAMES}


def _restore_project_return_context_if_needed(back_page: str) -> None:
    if back_page != "pages/projectItem.py":
        return
    if st.session_state.get("return_to_project_on_back"):
        st.session_state.project_view_id = st.session_state.get("return_project_view_id")
        st.session_state.return_to_project_on_back = False
        st.session_state.return_project_view_id = None


def _project_delete_guard_errors(*, data: dict, list_key: str, item_id: str) -> list[str]:
    guarded_projects: list[tuple[str, dict, list[str], list[str]]] = []
    if list_key == "actions":
        for project_id, project in data.setdefault("projects", {}).items():
            action_ids = list(project.get("action_ids", []))
            if item_id not in action_ids:
                continue
            guarded_projects.append(
                (
                    project_id,
                    project,
                    [action_id for action_id in action_ids if action_id != item_id],
                    list(project.get("delegation_ids", [])),
                )
            )
    elif list_key == "delegations":
        for project_id, project in data.setdefault("projects", {}).items():
            delegation_ids = list(project.get("delegation_ids", []))
            if item_id not in delegation_ids:
                continue
            guarded_projects.append(
                (
                    project_id,
                    project,
                    list(project.get("action_ids", [])),
                    [delegation_id for delegation_id in delegation_ids if delegation_id != item_id],
                )
            )

    errors: list[str] = []
    for project_id, project, action_ids, delegation_ids in guarded_projects:
        validation = validate_project_save(
            title=str(project.get("title", "") or ""),
            action_ids=action_ids,
            delegation_ids=delegation_ids,
        )
        if validation.ok:
            continue
        project_title = str(project.get("title", "") or "Untitled Project")
        errors.append(
            f"Cannot delete this item because it would violate project save rules for '{project_title}' ({project_id})."
        )
    return errors


def render_item_detail_form(
    *,
    data: dict,
    list_key: str,
    item_id: str | None,
    title_emoji: str,
    page_title: str,
    back_page: str,
    back_label: str,
    title_keys: list[str],
    subtitle_text: str,
    show_due_date: bool = False,
    date_label: str = "Due Date",
    date_field_candidates: list[str] | None = None,
    status_options: list[str] | None = None,
) -> None:
    items = data.setdefault(list_key, {})
    is_edit = item_id is not None and item_id in items
    date_field_candidates = date_field_candidates or DATE_FIELD_CANDIDATES
    status_options = status_options or DEFAULT_STATUS_OPTIONS

    original = _as_dict(items[item_id]) if is_edit else {}

    default_title = _pick(original, title_keys, "")
    default_details = _pick(original, ["details", "description", "notes"], "")
    default_status = _pick(original, ["status", "state"], status_options[0])
    default_due_date = _parse_iso_date(_pick(original, date_field_candidates, "")) if show_due_date else None

    st.title(f"{title_emoji} {page_title}")
    st.caption(subtitle_text if is_edit else f"Create a new {page_title.lower()}.")

    with st.form(f"{list_key}_detail_form"):
        title = st.text_input("Title", value=default_title)

        due_date_value = None
        if show_due_date:
            due_date_kwargs = {"value": default_due_date if default_due_date is not None else date.today()}
            if not is_edit:
                due_date_kwargs["min_value"] = date.today()
            due_date_value = st.date_input(date_label, **due_date_kwargs)

        details = st.text_area("Details", value=default_details, height=180)

        status = st.selectbox(
            "Status",
            status_options,
            index=_status_index(default_status, status_options),
        )

        action_cols = st.columns(3)
        save = action_cols[0].form_submit_button("Save Changes" if is_edit else "Create")
        delete = action_cols[1].form_submit_button("Delete", disabled=not is_edit)
        back = action_cols[2].form_submit_button("Back")

    index_key = f"{list_key[:-1]}_view_id"

    if back:
        st.session_state[index_key] = None
        _restore_project_return_context_if_needed(back_page)
        st.switch_page(back_page)
        return

    if delete and is_edit:
        delete_guard_errors = _project_delete_guard_errors(data=data, list_key=list_key, item_id=item_id)
        if delete_guard_errors:
            for error in delete_guard_errors:
                st.error(error)
            return

        if list_key == "actions":
            for project in data.setdefault("projects", {}).values():
                project["action_ids"] = [action_id for action_id in project.get("action_ids", []) if action_id != item_id]
        elif list_key == "delegations":
            for project in data.setdefault("projects", {}).values():
                project["delegation_ids"] = [delegation_id for delegation_id in project.get("delegation_ids", []) if delegation_id != item_id]
        del items[item_id]
        st.session_state[index_key] = None
        _restore_project_return_context_if_needed(back_page)
        st.switch_page(back_page)
        return

    if save:
        clean_title = title.strip()
        if not clean_title:
            st.error("Title is required.")
            return

        updated = deepcopy(original) if is_edit else {"id": new_uuid()}
        updated = _sanitize_source_keys(updated)
        updated[title_keys[0]] = clean_title

        if show_due_date and due_date_value is not None:
            _delete_known_date_keys(updated, date_field_candidates)
            updated[date_field_candidates[0]] = due_date_value.isoformat()

        updated["details"] = details.strip()
        updated["status"] = status

        if list_key == "actions":
            updated.setdefault("project_id", None)
            updated.setdefault("is_active_global", True)
        elif list_key == "delegations":
            updated.setdefault("project_id", None)
            updated.setdefault("is_active_global", True)

        target_id = item_id if is_edit else updated["id"]
        items[target_id] = updated

        st.session_state[index_key] = None
        _restore_project_return_context_if_needed(back_page)
        st.switch_page(back_page)
