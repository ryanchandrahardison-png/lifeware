from __future__ import annotations

from dataclasses import dataclass

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
