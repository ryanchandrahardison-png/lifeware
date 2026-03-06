from datetime import datetime, date, time
from zoneinfo import ZoneInfo

NY_TZ = ZoneInfo("America/New_York")
UTC_TZ = ZoneInfo("UTC")
DEFAULT_STATUS = "Scheduled"
ALLOWED_STATUSES = ["Scheduled", "Complete"]


def fmt_ny(dt_utc):
    dt_local = dt_utc.astimezone(NY_TZ)
    return dt_local.strftime("%d-%b-%Y %H:%M").upper()


def parse_dt_any(value):
    if not value or not isinstance(value, str):
        return None

    v = value.strip()
    if not v:
        return None

    try:
        iso = v
        if iso.endswith("Z"):
            iso = iso[:-1] + "+00:00"
        dt = datetime.fromisoformat(iso)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC_TZ)
        return dt.astimezone(UTC_TZ)
    except Exception:
        pass

    try:
        dt_local = datetime.strptime(v.upper(), "%d-%b-%Y %H:%M").replace(tzinfo=NY_TZ)
        return dt_local.astimezone(UTC_TZ)
    except Exception:
        return None


def combine_local_to_utc(start_date: date, start_time: time):
    dt_local = datetime.combine(start_date, start_time).replace(tzinfo=NY_TZ)
    return dt_local.astimezone(UTC_TZ)


def split_utc_to_local_parts(value, default_date=None, default_time=None):
    dt_utc = parse_dt_any(value)
    if dt_utc is None:
        return default_date, default_time
    dt_local = dt_utc.astimezone(NY_TZ)
    return dt_local.date(), dt_local.time().replace(second=0, microsecond=0)


def build_event_payload(title, description, status, start_date, start_time, end_date, end_time):
    status_value = status if status in ALLOWED_STATUSES else DEFAULT_STATUS
    start_utc = combine_local_to_utc(start_date, start_time)
    end_utc = combine_local_to_utc(end_date, end_time)
    return {
        "title": (title or "").strip(),
        "description": (description or "").strip(),
        "status": status_value,
        "start_utc": start_utc.isoformat(),
        "end_utc": end_utc.isoformat(),
    }


def normalize_calendar_event(ev):
    if not isinstance(ev, dict):
        return {
            "title": "",
            "description": "",
            "status": DEFAULT_STATUS,
            "start_utc": "",
            "end_utc": "",
        }

    normalized = {
        "title": ev.get("title", "") or "",
        "description": ev.get("description", "") or "",
        "status": ev.get("status", DEFAULT_STATUS) or DEFAULT_STATUS,
        "start_utc": ev.get("start_utc", "") or "",
        "end_utc": ev.get("end_utc", "") or "",
    }

    if normalized["status"] not in ALLOWED_STATUSES:
        normalized["status"] = DEFAULT_STATUS

    if not normalized["start_utc"]:
        dt = parse_dt_any(ev.get("start", ""))
        if dt:
            normalized["start_utc"] = dt.isoformat()

    if not normalized["end_utc"]:
        dt = parse_dt_any(ev.get("end", ""))
        if dt:
            normalized["end_utc"] = dt.isoformat()

    return normalized


def normalize_calendar_events(data):
    calendar = data.get("calendar", [])
    if not isinstance(calendar, list):
        data["calendar"] = []
        return
    data["calendar"] = [normalize_calendar_event(ev) for ev in calendar if isinstance(ev, dict)]
