from __future__ import annotations

from copy import deepcopy
from datetime import date
import uuid
from typing import Any

from core.calendar_utils import ensure_event_utc_fields

CANONICAL_COLLECTIONS = ("events", "actions", "delegations", "projects")


def new_uuid() -> str:
    return str(uuid.uuid4())


def is_completed_status(value: Any) -> bool:
    return str(value or "").strip().lower() in {"completed", "complete"}


def is_waiting_status(value: Any) -> bool:
    return str(value or "").strip().lower() == "waiting"


def action_is_active(item: dict) -> bool:
    return not is_completed_status(item.get("status")) and bool(item.get("is_active_global", True))


def delegation_is_active(item: dict) -> bool:
    return (
        not is_completed_status(item.get("status"))
        and bool(item.get("is_active_global", True))
    )


def _normalize_event(item: dict[str, Any]) -> dict[str, Any]:
    normalized = deepcopy(item)
    normalized.setdefault("id", new_uuid())
    normalized.setdefault("title", "")
    normalized.setdefault("details", normalized.get("description", ""))
    if "description" in normalized and "details" not in item:
        normalized.pop("description", None)
    ensure_event_utc_fields(normalized)
    return normalized


def _normalize_action(item: dict[str, Any]) -> dict[str, Any]:
    normalized = deepcopy(item)
    normalized.setdefault("id", new_uuid())
    normalized.setdefault("title", normalized.get("name") or normalized.get("action") or normalized.get("task") or "")
    normalized.setdefault("details", normalized.get("description") or normalized.get("notes") or "")
    if normalized.get("due") and not normalized.get("due_date"):
        normalized["due_date"] = normalized.get("due")
    normalized.setdefault("due_date", None)
    normalized.setdefault("status", normalized.get("state") or "Open")
    normalized.setdefault("project_id", None)
    normalized.setdefault("is_active_global", True)
    for key in ("name", "action", "task", "description", "notes", "state", "due", "when", "date"):
        if key not in {"title", "details", "status", "due_date"}:
            normalized.pop(key, None)
    return normalized


def _normalize_delegation(item: dict[str, Any]) -> dict[str, Any]:
    normalized = deepcopy(item)
    normalized.setdefault("id", new_uuid())
    normalized.setdefault("title", normalized.get("name") or normalized.get("task") or normalized.get("item") or "")
    normalized.setdefault("details", normalized.get("description") or normalized.get("notes") or "")
    for key in ("follow_up", "due", "when", "date", "due_date"):
        if normalized.get(key) and not normalized.get("follow_up_date"):
            normalized["follow_up_date"] = normalized.get(key)
            break
    normalized.setdefault("follow_up_date", None)
    normalized.setdefault("status", normalized.get("state") or "Waiting")
    normalized.setdefault("project_id", None)
    normalized.setdefault("is_active_global", True)
    for key in ("name", "task", "item", "description", "notes", "state", "follow_up", "due", "when", "date", "due_date"):
        if key not in {"title", "details", "status", "follow_up_date"}:
            normalized.pop(key, None)
    return normalized


def _normalize_project(item: dict[str, Any]) -> dict[str, Any]:
    normalized = deepcopy(item)
    normalized.setdefault("id", new_uuid())
    normalized.setdefault("title", "")
    normalized.setdefault("description", normalized.get("details", ""))
    normalized.setdefault("due_date", None)
    normalized.setdefault("status", "Active")
    normalized.setdefault("action_ids", [])
    normalized.setdefault("delegation_ids", [])
    normalized.pop("details", None)
    return normalized


def _dictify_collection(raw: Any, kind: str) -> dict[str, dict[str, Any]]:
    if isinstance(raw, dict):
        iterable = raw.values()
    elif isinstance(raw, list):
        iterable = raw
    else:
        iterable = []

    result: dict[str, dict[str, Any]] = {}
    for item in iterable:
        if not isinstance(item, dict):
            item = {"title": "" if item is None else str(item)}
        if kind == "events":
            normalized = _normalize_event(item)
        elif kind == "actions":
            normalized = _normalize_action(item)
        elif kind == "delegations":
            normalized = _normalize_delegation(item)
        else:
            normalized = _normalize_project(item)
        result[normalized["id"]] = normalized
    return result


def normalize_data(loaded: Any) -> dict[str, Any]:
    if not isinstance(loaded, dict):
        loaded = {}

    normalized = deepcopy(loaded)
    normalized["events"] = _dictify_collection(loaded.get("events", loaded.get("calendar", {})), "events")
    normalized["actions"] = _dictify_collection(loaded.get("actions", {}), "actions")
    normalized["delegations"] = _dictify_collection(loaded.get("delegations", {}), "delegations")
    normalized["projects"] = _dictify_collection(loaded.get("projects", {}), "projects")
    normalized.pop("calendar", None)
    return normalized


def ensure_integrity(data: dict[str, Any]) -> list[str]:
    warnings: list[str] = []
    data.setdefault("events", {})
    data.setdefault("actions", {})
    data.setdefault("delegations", {})
    data.setdefault("projects", {})

    projects = data["projects"]
    actions = data["actions"]
    delegations = data["delegations"]

    for project in projects.values():
        valid_action_ids = [aid for aid in project.get("action_ids", []) if aid in actions]
        if valid_action_ids != project.get("action_ids", []):
            warnings.append(f"Removed missing action references from project '{project.get('title', 'Untitled')}'.")
            project["action_ids"] = valid_action_ids

        valid_delegation_ids = [did for did in project.get("delegation_ids", []) if did in delegations]
        if valid_delegation_ids != project.get("delegation_ids", []):
            warnings.append(f"Removed missing delegation references from project '{project.get('title', 'Untitled')}'.")
            project["delegation_ids"] = valid_delegation_ids

    for action_id, action in list(actions.items()):
        project_id = action.get("project_id")
        if project_id and project_id not in projects:
            warnings.append(f"Converted action '{action.get('title', 'Untitled')}' to standalone because its project was missing.")
            action["project_id"] = None
            action["is_active_global"] = True
            continue
        if project_id and action_id not in projects[project_id].setdefault("action_ids", []):
            projects[project_id]["action_ids"].append(action_id)
            warnings.append(f"Repaired action link for '{action.get('title', 'Untitled')}'.")

    for delegation_id, delegation in list(delegations.items()):
        project_id = delegation.get("project_id")
        if project_id and project_id not in projects:
            warnings.append(f"Converted delegation '{delegation.get('title', 'Untitled')}' to standalone because its project was missing.")
            delegation["project_id"] = None
            delegation["is_active_global"] = True
            continue
        if project_id and delegation_id not in projects[project_id].setdefault("delegation_ids", []):
            projects[project_id]["delegation_ids"].append(delegation_id)
            warnings.append(f"Repaired delegation link for '{delegation.get('title', 'Untitled')}'.")

    for project_id, project in list(projects.items()):
        action_ids = []
        for action_id in project.get("action_ids", []):
            action = actions.get(action_id)
            if not action:
                continue
            action["project_id"] = project_id
            action_ids.append(action_id)
        project["action_ids"] = action_ids

        delegation_ids = []
        for delegation_id in project.get("delegation_ids", []):
            delegation = delegations.get(delegation_id)
            if not delegation:
                continue
            delegation["project_id"] = project_id
            delegation_ids.append(delegation_id)
        project["delegation_ids"] = delegation_ids

    return warnings


def parse_date_only(value: Any) -> date | None:
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


def linked_actions_for_project(data: dict[str, Any], project: dict[str, Any]) -> list[dict[str, Any]]:
    return [data["actions"][aid] for aid in project.get("action_ids", []) if aid in data.get("actions", {})]


def linked_delegations_for_project(data: dict[str, Any], project: dict[str, Any]) -> list[dict[str, Any]]:
    return [data["delegations"][did] for did in project.get("delegation_ids", []) if did in data.get("delegations", {})]


def project_health(data: dict[str, Any], project: dict[str, Any]) -> str:
    actions = linked_actions_for_project(data, project)
    delegations = linked_delegations_for_project(data, project)
    linked = actions + delegations
    if not linked:
        return "Stalled"
    if all(is_completed_status(item.get("status")) for item in linked):
        return "Ready to Complete"

    active_actions = [item for item in actions if action_is_active(item)]
    active_delegations = [item for item in delegations if delegation_is_active(item)]
    active_total = active_actions + active_delegations

    if active_actions:
        return "Healthy"
    if active_total and not active_actions:
        return "Blocked"
    return "Stalled"
