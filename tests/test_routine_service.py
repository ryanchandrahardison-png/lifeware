from datetime import date

from core.routine_service import empty_routine_draft, routine_draft_from_existing, save_routine_draft


def _valid_draft(title: str = "Routine A") -> dict:
    draft = empty_routine_draft()
    draft["title"] = title
    draft["cadence"] = "Daily"
    draft["start_time"] = "09:00"
    draft["tasks"] = [{"id": "t1", "title": "Task 1", "state": "pending", "postpone_until": None}]
    return draft


def test_new_routine_draft_not_saved_until_commit():
    routines: dict = {}
    draft = _valid_draft()

    assert routines == {}
    assert draft["id"] not in routines

    result = save_routine_draft(routines, draft, today=date(2026, 3, 23))
    assert result.ok
    assert len(routines) == 1
    assert result.routine_id in routines


def test_existing_routine_edit_draft_does_not_mutate_live_until_save():
    existing = _valid_draft("Original")
    existing_id = existing["id"]
    routines = {existing_id: existing}

    draft = routine_draft_from_existing(existing)
    draft["title"] = "Updated"

    assert routines[existing_id]["title"] == "Original"

    result = save_routine_draft(routines, draft, existing_routine_id=existing_id, today=date(2026, 3, 23))
    assert result.ok
    assert routines[existing_id]["title"] == "Updated"
