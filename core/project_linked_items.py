from __future__ import annotations

from datetime import date

from core.entities import parse_date_only


def linked_item_date(item: dict) -> date | None:
    return parse_date_only(item.get("due_date") or item.get("follow_up_date"))


def linked_item_group(item: dict) -> str:
    status = str(item.get("status", "")).strip().lower()
    if status == "completed":
        return "Completed"

    item_date = linked_item_date(item)
    if item_date is None:
        return "Floating"
    if item_date < date.today():
        return "Past Due"
    return "Upcoming"


def linked_item_type(item: dict) -> str:
    return "Delegation" if item.get("kind") == "delegation" else "Action"


def linked_item_sort_key(item: dict):
    item_date = linked_item_date(item)
    return (item_date is None, item_date or date.max, str(item.get("title", "")).lower())


def grouped_linked_items(linked_actions: list[dict], linked_delegations: list[dict]) -> dict[str, list[dict]]:
    grouped = {"Completed": [], "Past Due": [], "Upcoming": [], "Floating": []}
    merged = [{**item, "kind": "action"} for item in linked_actions] + [{**item, "kind": "delegation"} for item in linked_delegations]
    for item in merged:
        grouped[linked_item_group(item)].append(item)
    for key in ["Past Due", "Upcoming", "Floating"]:
        grouped[key] = sorted(grouped[key], key=linked_item_sort_key)
    return grouped


def is_next_action_item(item: dict) -> bool:
    if item.get("unresolved"):
        return False
    return bool(item.get("is_active_global", True))


def filter_linked_items_by_activity(
    grouped_items: dict[str, list[dict]],
    *,
    active: bool,
) -> dict[str, list[dict]]:
    filtered: dict[str, list[dict]] = {}
    for group, items in grouped_items.items():
        filtered[group] = [item for item in items if is_next_action_item(item) is active]
    return filtered


def count_grouped_items(grouped_items: dict[str, list[dict]]) -> int:
    return sum(len(items) for items in grouped_items.values())


def project_linked_items_with_unresolved(data: dict, project: dict) -> tuple[list[dict], list[dict]]:
    actions: list[dict] = []
    for action_id in project.get("action_ids", []):
        action = data.get("actions", {}).get(action_id)
        if action:
            actions.append(action)
        else:
            actions.append({"id": action_id, "title": "Missing Action", "status": "Open", "unresolved": True})

    delegations: list[dict] = []
    for delegation_id in project.get("delegation_ids", []):
        delegation = data.get("delegations", {}).get(delegation_id)
        if delegation:
            delegations.append(delegation)
        else:
            delegations.append({"id": delegation_id, "title": "Missing Delegation", "status": "Waiting", "unresolved": True})

    return actions, delegations


def linked_item_date_text(item: dict) -> str:
    item_date = linked_item_date(item)
    return item_date.isoformat() if item_date else "—"
