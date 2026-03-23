from __future__ import annotations

from core.project_linked_items import linked_item_date_text, linked_item_type


LINKED_ITEM_GROUP_ORDER = ("Completed", "Past Due", "Upcoming", "Floating")
MOBILE_USER_AGENT_TOKENS = ("iphone", "android", "mobile", "ipad")


def default_compact_view_from_user_agent(user_agent: str) -> bool:
    ua = str(user_agent or "").lower()
    return any(token in ua for token in MOBILE_USER_AGENT_TOKENS)


def linked_item_display_rows(items: list[dict]) -> list[dict]:
    return [
        {
            "Task Name": item.get("title", "Untitled"),
            "Type": linked_item_type(item),
            "Date": linked_item_date_text(item),
        }
        for item in items
    ]


def linked_item_compact_label(item: dict) -> str:
    task_name = item.get("title", "Untitled")
    task_type = linked_item_type(item)
    task_date = linked_item_date_text(item)
    return f"{task_name}  |  {task_type}  |  {task_date}"


def requires_draft_link_warning(*, item_id: object, draft: dict | None) -> bool:
    return not bool(item_id) and draft is not None
