from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
import calendar
from typing import Any

from core.entities import new_uuid

CADENCE_OPTIONS = ["Daily", "Weekly", "Monthly", "3-Month", "6-Month", "Yearly"]
TASK_STATE_PENDING = "pending"
TASK_STATE_COMPLETED = "completed"
TASK_STATE_POSTPONED = "postponed"
TASK_STATE_OPTIONS = [TASK_STATE_PENDING, TASK_STATE_COMPLETED, TASK_STATE_POSTPONED]


@dataclass
class ServiceResult:
    ok: bool
    errors: list[str] | None = None


def _parse_hhmm(value: str | None) -> time | None:
    if not value:
        return None
    try:
        parts = str(value).strip().split(":")
        if len(parts) != 2:
            return None
        return time(hour=int(parts[0]), minute=int(parts[1]))
    except Exception:
        return None


def _months_between(start: date, end: date) -> int:
    return (end.year - start.year) * 12 + (end.month - start.month)


def _add_months(d: date, months: int) -> date:
    month_index = (d.month - 1) + months
    year = d.year + month_index // 12
    month = (month_index % 12) + 1
    day = min(d.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def _window_for_today(cadence: str, today: date, routine: dict[str, Any]) -> tuple[date, date] | None:
    if cadence == "Daily":
        return today, today
    if cadence == "Weekly":
        start = today - timedelta(days=today.weekday())
        end = start + timedelta(days=6)
        return start, end
    if cadence == "Monthly":
        start = date(today.year, today.month, 1)
        end = date(today.year, today.month, calendar.monthrange(today.year, today.month)[1])
        return start, end
    if cadence in {"3-Month", "6-Month"}:
        anchor = _parse_date(routine.get("anchor_date"))
        if not anchor:
            return None
        interval = 3 if cadence == "3-Month" else 6
        months = _months_between(anchor, today)
        if months < 0:
            return None
        periods = months // interval
        start = _add_months(anchor, periods * interval)
        end = _add_months(start, interval) - timedelta(days=1)
        return start, end
    if cadence == "Yearly":
        start = date(today.year, 1, 1)
        end = date(today.year, 12, 31)
        return start, end
    return None


def _parse_date(value: Any) -> date | None:
    if value in (None, ""):
        return None
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value))
    except Exception:
        return None


def routine_due_today(routine: dict[str, Any], today: date | None = None) -> bool:
    today = today or date.today()
    cadence = str(routine.get("cadence") or "")
    if cadence == "Daily":
        return True
    if cadence == "Weekly":
        return routine.get("day_of_week") == today.weekday()
    if cadence == "Monthly":
        return int(routine.get("day_of_month") or 0) == today.day
    if cadence in {"3-Month", "6-Month"}:
        anchor = _parse_date(routine.get("anchor_date"))
        if not anchor:
            return False
        if today < anchor:
            return False
        interval = 3 if cadence == "3-Month" else 6
        return _months_between(anchor, today) % interval == 0 and today.day == anchor.day
    if cadence == "Yearly":
        anchor = _parse_date(routine.get("anchor_date"))
        return bool(anchor and today.month == anchor.month and today.day == anchor.day)
    return False


def routine_instance_key(routine: dict[str, Any], today: date | None = None) -> str | None:
    today = today or date.today()
    if not routine_due_today(routine, today=today):
        return None
    cadence = str(routine.get("cadence") or "")
    if cadence == "Daily":
        return today.isoformat()
    if cadence == "Weekly":
        y, w, _ = today.isocalendar()
        return f"{y}-W{w:02d}"
    if cadence == "Monthly":
        return f"{today.year}-{today.month:02d}"
    if cadence in {"3-Month", "6-Month"}:
        anchor = _parse_date(routine.get("anchor_date"))
        if not anchor:
            return None
        interval = 3 if cadence == "3-Month" else 6
        periods = _months_between(anchor, today) // interval
        return f"{cadence}:{anchor.isoformat()}:{periods}"
    if cadence == "Yearly":
        return str(today.year)
    return None


def validate_routine_payload(payload: dict[str, Any]) -> ServiceResult:
    errors: list[str] = []
    title = str(payload.get("title") or "").strip()
    cadence = str(payload.get("cadence") or "")
    start_time = str(payload.get("start_time") or "").strip()
    if not title:
        errors.append("Routine title is required.")
    if cadence not in CADENCE_OPTIONS:
        errors.append("Cadence is required.")
    if _parse_hhmm(start_time) is None:
        errors.append("Start time is required and must use HH:MM format.")

    if cadence == "Weekly" and payload.get("day_of_week") is None:
        errors.append("Weekly routines require a day of week.")
    if cadence == "Monthly":
        dom = int(payload.get("day_of_month") or 0)
        if dom < 1 or dom > 31:
            errors.append("Monthly routines require day-of-month (1-31).")
    if cadence in {"3-Month", "6-Month", "Yearly"} and not _parse_date(payload.get("anchor_date")):
        errors.append(f"{cadence} routines require an explicit anchor date.")

    tasks = payload.get("tasks", [])
    if not isinstance(tasks, list) or not tasks:
        errors.append("At least one routine subtask is required.")
    else:
        for task in tasks:
            if not str(task.get("title") or "").strip():
                errors.append("Routine subtasks require non-empty titles.")
                break
    return ServiceResult(ok=not errors, errors=errors)


def ensure_routine_shape(routine: dict[str, Any]) -> dict[str, Any]:
    routine.setdefault("id", new_uuid())
    routine.setdefault("title", "")
    routine.setdefault("cadence", "Daily")
    routine.setdefault("start_time", "09:00")
    routine.setdefault("day_of_week", None)
    routine.setdefault("day_of_month", None)
    routine.setdefault("anchor_date", None)
    routine.setdefault("tasks", [])
    routine.setdefault("active_instance_key", None)
    for task in routine["tasks"]:
        task.setdefault("id", new_uuid())
        task.setdefault("title", "")
        task.setdefault("state", TASK_STATE_PENDING)
        task.setdefault("postpone_until", None)
    return routine


def reset_due_instance_if_needed(routine: dict[str, Any], today: date | None = None) -> None:
    today = today or date.today()
    next_key = routine_instance_key(routine, today=today)
    if not next_key:
        return
    current = routine.get("active_instance_key")
    if current == next_key:
        return
    routine["active_instance_key"] = next_key
    for task in routine.get("tasks", []):
        task["state"] = TASK_STATE_PENDING
        task["postpone_until"] = None


def postpone_limit_datetime(routine: dict[str, Any], now: datetime | None = None) -> datetime | None:
    now = now or datetime.now()
    window = _window_for_today(str(routine.get("cadence") or ""), now.date(), routine)
    if not window:
        return None
    _, end_date = window
    return datetime.combine(end_date, time(23, 59))


def apply_postpone(task: dict[str, Any], routine: dict[str, Any], *, days: int, hours: int, minutes: int, now: datetime | None = None) -> ServiceResult:
    now = now or datetime.now()
    total = timedelta(days=max(days, 0), hours=max(hours, 0), minutes=max(minutes, 0))
    if total <= timedelta(0):
        return ServiceResult(ok=False, errors=["Postpone duration must be greater than zero."])

    target = now + total
    max_dt = postpone_limit_datetime(routine, now=now)
    if max_dt and target > max_dt:
        return ServiceResult(ok=False, errors=["Postpone target exceeds this cadence window."])

    task["state"] = TASK_STATE_POSTPONED
    task["postpone_until"] = target.isoformat(timespec="minutes")
    return ServiceResult(ok=True)
