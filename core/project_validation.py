from __future__ import annotations

from datetime import date
from typing import Any

from core.entities import is_completed_status
from core.project_types import ServiceResult


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


def validate_project_due_date_change(*, selected_due_date: date | None, original_due_date: date | None) -> ServiceResult:
    if selected_due_date and selected_due_date < date.today() and selected_due_date != original_due_date:
        return ServiceResult(ok=False, errors=["Project Due Date cannot be in the past unless it is unchanged."])
    return ServiceResult(ok=True)


def validate_linked_item_date_change(*, selected_date: date | None, original_date: date | None, date_label: str) -> ServiceResult:
    if selected_date and selected_date < date.today() and selected_date != original_date:
        return ServiceResult(ok=False, errors=[f"{date_label} cannot be in the past unless it is unchanged."])
    return ServiceResult(ok=True)
