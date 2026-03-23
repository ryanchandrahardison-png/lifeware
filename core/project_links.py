from __future__ import annotations

from typing import Any

from core.entities import new_uuid
from core.project_types import ServiceResult


def create_linked_action(*, data: dict[str, Any], project_id: str, title: str, details: str, due_date: str | None, is_active_global: bool) -> str:
    action_id = new_uuid()
    data["actions"][action_id] = {
        "id": action_id,
        "title": str(title or "").strip(),
        "details": str(details or "").strip(),
        "due_date": due_date,
        "status": "Open",
        "project_id": project_id,
        "is_active_global": bool(is_active_global),
    }
    data["projects"][project_id].setdefault("action_ids", []).append(action_id)
    return action_id


def create_linked_delegation(*, data: dict[str, Any], project_id: str, title: str, details: str, follow_up_date: str | None, is_active_global: bool) -> str:
    delegation_id = new_uuid()
    data["delegations"][delegation_id] = {
        "id": delegation_id,
        "title": str(title or "").strip(),
        "details": str(details or "").strip(),
        "follow_up_date": follow_up_date,
        "status": "Waiting",
        "project_id": project_id,
        "is_active_global": bool(is_active_global),
    }
    data["projects"][project_id].setdefault("delegation_ids", []).append(delegation_id)
    return delegation_id


def remove_project_link_reference(
    *,
    data: dict[str, Any],
    project_id: str,
    item_type: str,
    item_id: str,
) -> ServiceResult:
    project = data.get("projects", {}).get(project_id)
    if not project:
        return ServiceResult(ok=False, errors=["Project not found."])

    if item_type == "action":
        project["action_ids"] = [aid for aid in project.get("action_ids", []) if aid != item_id]
        action = data.get("actions", {}).get(item_id)
        if action and action.get("project_id") == project_id:
            action["project_id"] = None
            action["is_active_global"] = True
        return ServiceResult(ok=True, message="Action link removed from project.")

    if item_type == "delegation":
        project["delegation_ids"] = [did for did in project.get("delegation_ids", []) if did != item_id]
        delegation = data.get("delegations", {}).get(item_id)
        if delegation and delegation.get("project_id") == project_id:
            delegation["project_id"] = None
            delegation["is_active_global"] = True
        return ServiceResult(ok=True, message="Delegation link removed from project.")

    return ServiceResult(ok=False, errors=["Invalid linked-item type."])
