from datetime import date

from core.project_item_logic import (
    build_draft_action_payload,
    build_draft_delegation_payload,
    build_project_action_payload,
)


def test_build_draft_action_payload_normalizes_fields():
    editor = {
        "title": "  Action  ",
        "details": "  Details  ",
        "date": date(2026, 3, 25),
        "active_global": True,
    }

    payload = build_draft_action_payload(editor)
    assert payload == {
        "title": "Action",
        "details": "Details",
        "due_date": "2026-03-25",
        "status": "Open",
        "is_active_global": True,
    }


def test_build_draft_delegation_payload_uses_follow_up_date():
    editor = {"title": "Del", "details": "", "date": None, "active_global": False}
    payload = build_draft_delegation_payload(editor)
    assert payload["title"] == "Del"
    assert payload["follow_up_date"] is None
    assert payload["status"] == "Waiting"


def test_build_project_action_payload_matches_link_service_shape():
    editor = {"title": "A", "details": "B", "date": date(2026, 3, 28), "active_global": False}
    payload = build_project_action_payload(editor)
    assert payload["title"] == "A"
    assert payload["details"] == "B"
    assert payload["due_date"] == "2026-03-28"
    assert payload["is_active_global"] is False
