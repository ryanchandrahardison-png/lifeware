from datetime import datetime, date, time
from zoneinfo import ZoneInfo

NY_TZ = ZoneInfo("America/New_York")
UTC_TZ = ZoneInfo("UTC")


def fmt_ny(dt_utc: datetime) -> str:
    dt_local = dt_utc.astimezone(NY_TZ)
    return dt_local.strftime("%d-%b-%Y %H:%M").upper()


def parse_dt_any(value):
    if not value or not isinstance(value, str):
        return None

    v = value.strip()
    if not v:
        return None

    try:
        iso = v[:-1] + "+00:00" if v.endswith("Z") else v
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


def local_parts_to_utc(d: date, t: time) -> str:
    dt_local = datetime.combine(d, t).replace(tzinfo=NY_TZ)
    return dt_local.astimezone(UTC_TZ).isoformat()


def utc_to_local_parts(value):
    dt_utc = parse_dt_any(value)
    if not dt_utc:
        return None, None
    dt_local = dt_utc.astimezone(NY_TZ)
    return dt_local.date(), dt_local.time().replace(second=0, microsecond=0)


def normalize_calendar_event(ev):
    if not isinstance(ev, dict):
        return {
            "title": "",
            "description": "",
            "status": "Scheduled",
            "start_utc": "",
            "end_utc": "",
        }

    start_utc = ev.get("start_utc", "")
    end_utc = ev.get("end_utc", "")

    if not start_utc:
        parsed = parse_dt_any(ev.get("start", ""))
        start_utc = parsed.isoformat() if parsed else ""

    if not end_utc:
        parsed = parse_dt_any(ev.get("end", ""))
        end_utc = parsed.isoformat() if parsed else ""

    return {
        "title": ev.get("title", ""),
        "description": ev.get("description", ""),
        "status": ev.get("status", "Scheduled") or "Scheduled",
        "start_utc": start_utc,
        "end_utc": end_utc,
    }


def normalize_calendar_events(events):
    return [normalize_calendar_event(ev) for ev in events if isinstance(ev, dict)]


def build_calendar_event_payload(title, description, status, start_date, start_time, end_date, end_time):
    return {
        "title": title.strip(),
        "description": description,
        "status": status,
        "start_utc": local_parts_to_utc(start_date, start_time),
        "end_utc": local_parts_to_utc(end_date, end_time),
    }
