from datetime import date, datetime, time
from zoneinfo import ZoneInfo

from core.calendar_event_logic import (
    build_event_payload,
    normalize_event_datetimes,
    round_up_to_next_slot,
    validate_event_submission,
)


def test_round_up_to_next_slot_half_hour():
    value = datetime(2026, 3, 23, 9, 7)
    rounded = round_up_to_next_slot(value, 30)
    assert rounded == datetime(2026, 3, 23, 9, 30)


def test_normalize_event_datetimes_returns_utc_and_parsed_values():
    editor = {
        "start_date": date(2026, 3, 23),
        "start_time": time(9, 0),
        "end_date": date(2026, 3, 23),
        "end_time": time(9, 30),
    }
    start_utc, end_utc, start_dt, end_dt = normalize_event_datetimes(editor=editor)

    assert start_utc.endswith("+00:00")
    assert end_utc.endswith("+00:00")
    assert start_dt is not None
    assert end_dt is not None
    assert end_dt > start_dt


def test_validate_event_submission_for_new_event_checks_time_and_title():
    now_utc = datetime(2026, 3, 23, 14, 0, tzinfo=ZoneInfo("UTC"))
    errors = validate_event_submission(
        is_edit=False,
        title="   ",
        start_dt=datetime(2026, 3, 23, 13, 0, tzinfo=ZoneInfo("UTC")),
        end_dt=datetime(2026, 3, 23, 12, 0, tzinfo=ZoneInfo("UTC")),
        now_utc=now_utc,
    )
    assert "Start time cannot be before the current date/time." in errors
    assert "End time must be after start time." in errors
    assert "Title is required." in errors


def test_build_event_payload_keeps_existing_id_for_edits():
    payload = build_event_payload(
        event_id="ev-1",
        is_edit=True,
        title=" Meeting ",
        description=" Notes ",
        status="Scheduled",
        start_utc="2026-03-23T13:00:00+00:00",
        end_utc="2026-03-23T13:30:00+00:00",
    )
    assert payload["id"] == "ev-1"
    assert payload["title"] == "Meeting"
    assert payload["details"] == "Notes"
