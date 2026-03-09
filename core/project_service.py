from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any

from core.entities import is_completed_status, new_uuid

DELETE_CHOICE_CONVERT = "Convert linked items to standalone items"
DELETE_CHOICE_DELETE = "Delete linked items with the project"
DELETE_CHOICE_CANCEL = "Cancel deletion"
DELETE_CHOICE_OPTIONS = [
    DELETE_CHOICE_CONVERT,
    DELETE_CHOICE_DELETE,
    DELETE_CHOICE_CANCEL,
]


@dataclass
class ServiceResult:
    ok: bool
    message: str = ""
    errors: list[str] | None = None
    project_id: str | None = None


@dataclass
class DeleteResult(ServiceResult):
    deleted: bool = False
    requires_choice: bool = False


def _linked_count(action_ids: list[str], delegation_ids: list[str]) -> int:
    return len(action_ids) + len(delegation_ids)


def validate_project_save(*, title: str, action_ids: list[str], delegation_ids: list[str]) -> ServiceResult:
    errors: list[str] = []
    if not str(title or "").strip():
        errors.append("Project title is required.")
    if _linked_count(action_ids, delegation_ids) < 2:
        errors.append("A project requires at least 2 linked items total before it can be saved.")
    return ServiceResult(ok=not errors, errors=errors)


def validate_project_completion(*, status: str, linked_actions: list[dict[str, Any]], linked_delegations: list[dict[str, Any]]) -> ServiceResult:
    if str(status or "") != "Completed":
        return ServiceResult(ok=True)
    incomplete = [item for item in linked_actions + linked_delegations if not is_completed_status(item.get("status"))]
    if incomplete:
        return ServiceResult(
            ok=False,
            errors=["Project cannot be marked Completed until all linked actions and delegations are completed."],
        )
    return ServiceResult(ok=True)


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


def save_new_project(*, data: dict[str, Any], draft: dict[str, Any]) -> ServiceResult:
    action_drafts = list(draft.get("draft_actions", []))
    delegation_drafts = list(draft.get("draft_delegations", []))
    validation = validate_project_save(
        title=draft.get("title", ""),
        action_ids=[f"draft-action-{i}" for i in range(len(action_drafts))],
        delegation_ids=[f"draft-delegation-{i}" for i in range(len(delegation_drafts))],
    )
    if not validation.ok:
        return validation

    project_id = new_uuid()
    action_ids: list[str] = []
    delegation_ids: list[str] = []

    for action in action_drafts:
        action_id = new_uuid()
        payload = deepcopy(action)
        payload.update({"id": action_id, "project_id": project_id})
        data["actions"][action_id] = payload
        action_ids.append(action_id)

    for delegation in delegation_drafts:
        delegation_id = new_uuid()
        payload = deepcopy(delegation)
        payload.update({"id": delegation_id, "project_id": project_id})
        data["delegations"][delegation_id] = payload
        delegation_ids.append(delegation_id)

    data["projects"][project_id] = {
        "id": project_id,
        "title": str(draft.get("title", "")).strip(),
        "description": str(draft.get("description", "")).strip(),
        "due_date": draft.get("due_date"),
        "status": draft.get("status", "Active"),
        "action_ids": action_ids,
        "delegation_ids": delegation_ids,
    }
    return ServiceResult(ok=True, message="Project saved.", project_id=project_id)


def update_project(*, project: dict[str, Any], title: str, description: str, due_date: str | None, status: str, linked_actions: list[dict[str, Any]], linked_delegations: list[dict[str, Any]]) -> ServiceResult:
    save_validation = validate_project_save(
        title=title,
        action_ids=list(project.get("action_ids", [])),
        delegation_ids=list(project.get("delegation_ids", [])),
    )
    if not save_validation.ok:
        return save_validation

    completion_validation = validate_project_completion(
        status=status,
        linked_actions=linked_actions,
        linked_delegations=linked_delegations,
    )
    if not completion_validation.ok:
        return completion_validation

    project["title"] = str(title or "").strip()
    project["description"] = str(description or "").strip()
    project["due_date"] = due_date
    project["status"] = status
    return ServiceResult(ok=True, message="Project updated.")


def delete_project(*, data: dict[str, Any], project_id: str, choice: str) -> DeleteResult:
    project = data["projects"].get(project_id)
    if not project:
        return DeleteResult(ok=False, deleted=False, errors=["Project not found."])

    if choice == DELETE_CHOICE_CANCEL:
        return DeleteResult(ok=True, deleted=False, message="Project deletion canceled.")

    if choice == DELETE_CHOICE_CONVERT:
        for action_id in project.get("action_ids", []):
            if action_id in data["actions"]:
                data["actions"][action_id]["project_id"] = None
                data["actions"][action_id]["is_active_global"] = True
        for delegation_id in project.get("delegation_ids", []):
            if delegation_id in data["delegations"]:
                data["delegations"][delegation_id]["project_id"] = None
                data["delegations"][delegation_id]["is_active_global"] = True
    elif choice == DELETE_CHOICE_DELETE:
        for action_id in project.get("action_ids", []):
            data["actions"].pop(action_id, None)
        for delegation_id in project.get("delegation_ids", []):
            data["delegations"].pop(delegation_id, None)
    else:
        return DeleteResult(ok=False, deleted=False, errors=["Invalid project deletion choice."])

    data["projects"].pop(project_id, None)
    return DeleteResult(ok=True, deleted=True, message="Project deleted.")


def request_project_delete(*, data: dict[str, Any], project_id: str) -> DeleteResult:
    project = data.get("projects", {}).get(project_id)
    if not project:
        return DeleteResult(ok=False, deleted=False, errors=["Project not found."])
    has_linked = bool(project.get("action_ids") or project.get("delegation_ids"))
    if has_linked:
        return DeleteResult(ok=True, deleted=False, requires_choice=True)
    return delete_project(data=data, project_id=project_id, choice=DELETE_CHOICE_DELETE)


def save_project_from_draft(*, data: dict[str, Any], draft: dict[str, Any]) -> ServiceResult:
    return save_new_project(data=data, draft=draft)


def update_project_from_editor(
    *,
    data: dict[str, Any],
    project_id: str,
    title: str,
    description: str,
    due_date: str | None,
    status: str,
) -> ServiceResult:
    project = data.get("projects", {}).get(project_id)
    if not project:
        return ServiceResult(ok=False, errors=["Project not found."])

    linked_actions = [data["actions"][aid] for aid in project.get("action_ids", []) if aid in data.get("actions", {})]
    linked_delegations = [
        data["delegations"][did] for did in project.get("delegation_ids", []) if did in data.get("delegations", {})
    ]
    return update_project(
        project=project,
        title=title,
        description=description,
        due_date=due_date,
        status=status,
        linked_actions=linked_actions,
        linked_delegations=linked_delegations,
    )
