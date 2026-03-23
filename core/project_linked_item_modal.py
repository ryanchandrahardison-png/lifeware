from __future__ import annotations

from datetime import date

from core.entities import parse_date_only


def linked_item_modal_context(modal_item: dict) -> dict:
    kind = "delegation" if modal_item.get("kind") == "delegation" else "action"
    is_delegation = kind == "delegation"
    return {
        "kind": kind,
        "item_id": modal_item.get("id"),
        "collection_key": "delegations" if is_delegation else "actions",
        "date_field": "follow_up_date" if is_delegation else "due_date",
        "date_label": "Follow Up Date" if is_delegation else "Due Date",
        "status_options": ["Waiting", "Completed"] if is_delegation else ["Open", "Completed"],
    }


def modal_editor_key(kind: str, item_id: str | None) -> str:
    return f"project_linked_modal_editor::{kind}::{item_id}"


def modal_widget_keys(editor_key: str) -> dict[str, str]:
    return {
        "title": f"{editor_key}::title",
        "date": f"{editor_key}::date",
        "details": f"{editor_key}::details",
        "status": f"{editor_key}::status",
    }


def normalize_modal_status(status: object, status_options: list[str]) -> str:
    value = str(status or status_options[0])
    return value if value in status_options else status_options[0]


def min_linked_item_date(*, original_value, current_value, today: date | None = None) -> date:
    baseline_today = today or date.today()
    original_date = parse_date_only(original_value)
    current_date = parse_date_only(current_value)
    if original_date and original_date < baseline_today and current_date == original_date:
        return original_date
    return baseline_today
