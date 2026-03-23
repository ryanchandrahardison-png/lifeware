from datetime import date

from core.project_linked_item_modal import (
    linked_item_modal_context,
    min_linked_item_date,
    modal_editor_key,
    modal_widget_keys,
    normalize_modal_status,
)


def test_linked_item_modal_context_for_action_defaults():
    context = linked_item_modal_context({"kind": "action", "id": "a1"})
    assert context == {
        "kind": "action",
        "item_id": "a1",
        "collection_key": "actions",
        "date_field": "due_date",
        "date_label": "Due Date",
        "status_options": ["Open", "Completed"],
    }


def test_linked_item_modal_context_for_delegation():
    context = linked_item_modal_context({"kind": "delegation", "id": "d1"})
    assert context["collection_key"] == "delegations"
    assert context["date_field"] == "follow_up_date"
    assert context["status_options"] == ["Waiting", "Completed"]


def test_modal_editor_keys_and_widget_keys_are_stable():
    editor_key = modal_editor_key("action", "a1")
    assert editor_key == "project_linked_modal_editor::action::a1"
    keys = modal_widget_keys(editor_key)
    assert keys["title"].endswith("::title")
    assert keys["date"].endswith("::date")


def test_normalize_modal_status_falls_back_to_default():
    assert normalize_modal_status("Unknown", ["Open", "Completed"]) == "Open"
    assert normalize_modal_status("Completed", ["Open", "Completed"]) == "Completed"


def test_min_linked_item_date_keeps_original_past_date_when_unchanged():
    today = date(2026, 3, 23)
    assert min_linked_item_date(
        original_value=date(2026, 3, 10),
        current_value=date(2026, 3, 10),
        today=today,
    ) == date(2026, 3, 10)


def test_min_linked_item_date_uses_today_when_date_changes():
    today = date(2026, 3, 23)
    assert min_linked_item_date(
        original_value=date(2026, 3, 10),
        current_value=date(2026, 3, 11),
        today=today,
    ) == today
