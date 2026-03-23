from __future__ import annotations

from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from core.calendar_utils import ensure_event_utc_fields, local_to_utc_iso, parse_dt_any, utc_to_local_parts
from core.entities import new_uuid

DEFAULT_STATUS_OPTIONS = ["Scheduled", "Complete"]
UTC_TZ = ZoneInfo("UTC")


def round_up_to_next_slot(value: datetime, minutes: int = 30) -> datetime:
    floored = value.replace(second=0, microsecond=0)
    remainder = floored.minute % minutes
    if remainder == 0:
        return floored
    return floored + timedelta(minutes=(minutes - remainder))


def time_options(step_minutes: int = 30) -> list[time]:
    options: list[time] = []
    current = datetime.combine(date.today(), time(0, 0))
    end = current + timedelta(days=1)
    while current < end:
        options.append(current.time().replace(second=0, microsecond=0))
        current += timedelta(minutes=step_minutes)
    return options


def format_time_label(value: time) -> str:
    return datetime.combine(date.today(), value).strftime("%I:%M %p")


def time_index(options: list[time], selected: time) -> int:
    selected_clean = selected.replace(second=0, microsecond=0)
    if selected_clean in options:
        return options.index(selected_clean)

    selected_minutes = selected_clean.hour * 60 + selected_clean.minute
    for i, option in enumerate(options):
        option_minutes = option.hour * 60 + option.minute
        if option_minutes >= selected_minutes:
            return i
    return max(0, len(options) - 1)


def default_event_form_values(event: dict | None) -> dict:
    values = {
        "title": "",
        "description": "",
        "status": "Scheduled",
        "start_date": date.today(),
        "start_time": time(9, 0),
        "end_date": date.today(),
        "end_time": time(9, 30),
        "confirm_delete": False,
    }

    if not isinstance(event, dict):
        return values

    ensure_event_utc_fields(event)
    values["title"] = event.get("title", "")
    values["description"] = event.get("details", event.get("description", ""))
    values["status"] = event.get("status", "Scheduled")

    start_dt = parse_dt_any(event.get("start_utc")) or parse_dt_any(event.get("start"))
    end_dt = parse_dt_any(event.get("end_utc")) or parse_dt_any(event.get("end"))

    if start_dt:
        values["start_date"], values["start_time"] = utc_to_local_parts(start_dt)
    if end_dt:
        values["end_date"], values["end_time"] = utc_to_local_parts(end_dt)

    return values


def normalize_event_datetimes(*, editor: dict) -> tuple[str, str, datetime | None, datetime | None]:
    start_utc = local_to_utc_iso(editor.get("start_date"), editor.get("start_time"))
    end_utc = local_to_utc_iso(editor.get("end_date"), editor.get("end_time"))
    return start_utc, end_utc, parse_dt_any(start_utc), parse_dt_any(end_utc)


def validate_event_submission(*, is_edit: bool, title: str, start_dt: datetime | None, end_dt: datetime | None, now_utc: datetime) -> list[str]:
    errors: list[str] = []
    if not is_edit:
        if start_dt and start_dt < now_utc:
            errors.append("Start time cannot be before the current date/time.")
        if not start_dt or not end_dt or end_dt <= start_dt:
            errors.append("End time must be after start time.")

    if not title.strip():
        errors.append("Title is required.")
    return errors


def build_event_payload(*, event_id: str | None, is_edit: bool, title: str, description: str, status: str, start_utc: str, end_utc: str) -> dict:
    return {
        "id": event_id if is_edit and event_id else new_uuid(),
        "title": title.strip(),
        "details": description.strip(),
        "status": status,
        "start_utc": start_utc,
        "end_utc": end_utc,
    }
