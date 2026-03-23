from __future__ import annotations

from copy import deepcopy
from datetime import date
from typing import Any

from core.entities import new_uuid
from core.project_validation import validate_project_save

DEFAULT_STATUS_OPTIONS = ["Open", "Completed"]
DELEGATION_STATUS_OPTIONS = ["Waiting", "Completed"]
DATE_FIELD_CANDIDATES = ["due_date"]
FOLLOW_UP_FIELD_CANDIDATES = ["follow_up_date"]
SOURCE_FIELD_NAMES = {"source"}


def item_editor_config(list_key: str) -> dict:
    if list_key == "delegations":
        return {
            "date_label": "Follow Up Date",
            "date_field_candidates": FOLLOW_UP_FIELD_CANDIDATES,
            "status_options": DELEGATION_STATUS_OPTIONS,
        }
    return {
        "date_label": "Due Date",
        "date_field_candidates": DATE_FIELD_CANDIDATES,
        "status_options": DEFAULT_STATUS_OPTIONS,
    }


def as_dict(item: Any) -> dict:
    return deepcopy(item) if isinstance(item, dict) else {"title": "" if item is None else str(item)}


def pick_first(record: dict, keys: list[str], default: str = "") -> str:
    for key in keys:
        value = record.get(key)
        if value not in (None, ""):
            return str(value)
    return default


def parse_iso_date(value: Any) -> date | None:
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


def status_index(status: str, options: list[str]) -> int:
    if status in options:
        return options.index(status)
    lowered = status.lower()
    for i, option in enumerate(options):
        if option.lower() == lowered:
            return i
    return 0


def delete_known_date_keys(record: dict, field_candidates: list[str]) -> None:
    for key in field_candidates:
        record.pop(key, None)


def sanitize_source_keys(record: dict) -> dict:
    return {k: v for k, v in record.items() if k not in SOURCE_FIELD_NAMES}


def restore_project_return_context(*, session_state: dict, back_page: str) -> None:
    if back_page != "pages/projectItem.py":
        return
    if session_state.get("return_to_project_on_back"):
        session_state["project_view_id"] = session_state.get("return_project_view_id")
        session_state["return_to_project_on_back"] = False
        session_state["return_project_view_id"] = None


def detail_index_key(list_key: str) -> str:
    return f"{list_key[:-1]}_view_id"


def project_delete_guard_errors(*, data: dict, list_key: str, item_id: str) -> list[str]:
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


def delete_item_with_project_guard(*, data: dict, list_key: str, item_id: str) -> tuple[bool, list[str]]:
    items = data.setdefault(list_key, {})
    if item_id not in items:
        return False, ["Item not found."]

    delete_guard_errors = project_delete_guard_errors(data=data, list_key=list_key, item_id=item_id)
    if delete_guard_errors:
        return False, delete_guard_errors

    if list_key == "actions":
        for project in data.setdefault("projects", {}).values():
            project["action_ids"] = [action_id for action_id in project.get("action_ids", []) if action_id != item_id]
    elif list_key == "delegations":
        for project in data.setdefault("projects", {}).values():
            project["delegation_ids"] = [delegation_id for delegation_id in project.get("delegation_ids", []) if delegation_id != item_id]

    del items[item_id]
    return True, []


def save_item_with_constraints(
    *,
    data: dict,
    list_key: str,
    item_id: str | None,
    title: str,
    details: str,
    status: str,
    date_value: date | None,
    date_field_candidates: list[str] | None = None,
) -> tuple[bool, list[str], dict | None]:
    items = data.setdefault(list_key, {})
    is_edit = item_id is not None and item_id in items
    date_field_candidates = date_field_candidates or DATE_FIELD_CANDIDATES
    original = as_dict(items[item_id]) if is_edit else {}

    clean_title = str(title or "").strip()
    if not clean_title:
        return False, ["Title is required."], None

    updated = deepcopy(original) if is_edit else {"id": new_uuid()}
    updated = sanitize_source_keys(updated)
    updated["title"] = clean_title

    if date_value is not None:
        delete_known_date_keys(updated, date_field_candidates)
        updated[date_field_candidates[0]] = date_value.isoformat()

    updated["details"] = str(details or "").strip()
    updated["status"] = str(status or "").strip()

    if list_key in {"actions", "delegations"}:
        updated.setdefault("project_id", None)
        updated.setdefault("is_active_global", True)

    target_id = item_id if is_edit else updated["id"]
    items[target_id] = updated
    return True, [], deepcopy(updated)


def build_item_defaults(
    *,
    original: dict,
    title_keys: list[str],
    status_options: list[str],
    show_due_date: bool,
    date_field_candidates: list[str],
) -> dict:
    return {
        "title": pick_first(original, title_keys, ""),
        "details": pick_first(original, ["details", "description", "notes"], ""),
        "status": pick_first(original, ["status", "state"], status_options[0]),
        "due_date": parse_iso_date(pick_first(original, date_field_candidates, "")) if show_due_date else None,
    }


def build_item_snapshot(*, item_id: str | None, defaults: dict, is_edit: bool) -> tuple:
    due_date = defaults.get("due_date")
    return (
        item_id,
        defaults.get("title", ""),
        defaults.get("details", ""),
        defaults.get("status", ""),
        due_date.isoformat() if isinstance(due_date, date) else "",
        bool(is_edit),
    )
