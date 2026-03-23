from datetime import date

from core.item_detail_logic import (
    build_item_defaults,
    build_item_snapshot,
    restore_project_return_context,
    save_item_with_constraints,
)


def test_build_item_defaults_reads_aliases_and_due_date():
    original = {
        "name": "ignored",
        "title": "Action",
        "description": "Desc",
        "state": "Open",
        "due_date": "2026-03-15",
    }

    defaults = build_item_defaults(
        original=original,
        title_keys=["title", "name"],
        status_options=["Open", "Completed"],
        show_due_date=True,
        date_field_candidates=["due_date"],
    )

    assert defaults["title"] == "Action"
    assert defaults["details"] == "Desc"
    assert defaults["status"] == "Open"
    assert defaults["due_date"] == date(2026, 3, 15)


def test_save_item_constraints_preserves_unknown_fields_and_sanitizes_source():
    data = {
        "actions": {
            "a1": {
                "id": "a1",
                "title": "Old",
                "details": "Old details",
                "status": "Open",
                "due_date": "2026-03-20",
                "custom": "keep",
                "source": "remove",
            }
        }
    }

    ok, errors, updated = save_item_with_constraints(
        data=data,
        list_key="actions",
        item_id="a1",
        title=" New ",
        details=" Updated ",
        status="Completed",
        date_value=date(2026, 3, 22),
    )

    assert ok is True
    assert errors == []
    assert updated is not None
    assert updated["title"] == "New"
    assert updated["details"] == "Updated"
    assert updated["due_date"] == "2026-03-22"
    assert updated["custom"] == "keep"
    assert "source" not in updated


def test_build_snapshot_encodes_due_date():
    snapshot = build_item_snapshot(
        item_id="x1",
        defaults={"title": "T", "details": "D", "status": "Open", "due_date": date(2026, 3, 1)},
        is_edit=True,
    )
    assert snapshot == ("x1", "T", "D", "Open", "2026-03-01", True)


def test_restore_project_return_context_only_when_back_to_project():
    state = {
        "return_to_project_on_back": True,
        "return_project_view_id": "p7",
        "project_view_id": None,
    }
    restore_project_return_context(session_state=state, back_page="pages/projectItem.py")

    assert state["project_view_id"] == "p7"
    assert state["return_to_project_on_back"] is False
    assert state["return_project_view_id"] is None
