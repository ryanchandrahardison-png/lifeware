from datetime import datetime, date, time
from zoneinfo import ZoneInfo

NY_TZ = ZoneInfo("America/New_York")
UTC_TZ = ZoneInfo("UTC")
VALID_STATUSES = ["Scheduled", "Complete"]


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



def utc_to_local_parts(dt_utc: datetime):
    dt_local = dt_utc.astimezone(NY_TZ)
    return dt_local.date(), dt_local.time().replace(second=0, microsecond=0)



def local_to_utc_iso(d: date, t: time) -> str:
    dt_local = datetime.combine(d, t).replace(tzinfo=NY_TZ)
    return dt_local.astimezone(UTC_TZ).isoformat()



def build_calendar_event_payload(
    title: str,
    description: str,
    status: str,
    start_date: date,
    start_time: time,
    end_date: date,
    end_time: time,
) -> dict:
    normalized_status = status if status in VALID_STATUSES else "Scheduled"
    return {
        "title": title.strip(),
        "description": description.strip(),
        "status": normalized_status,
        "start_utc": local_to_utc_iso(start_date, start_time),
        "end_utc": local_to_utc_iso(end_date, end_time),
    }



def normalize_calendar_event(ev: dict) -> dict:
    if not isinstance(ev, dict):
        return {
            "title": "",
            "description": "",
            "status": "Scheduled",
            "start_utc": "",
            "end_utc": "",
        }

    start_dt = parse_dt_any(ev.get("start_utc")) or parse_dt_any(ev.get("start"))
    end_dt = parse_dt_any(ev.get("end_utc")) or parse_dt_any(ev.get("end"))
    status = ev.get("status", "Scheduled")
    if status not in VALID_STATUSES:
        status = "Scheduled"

    return {
        "title": str(ev.get("title", "") or "").strip(),
        "description": str(ev.get("description", "") or "").strip(),
        "status": status,
        "start_utc": start_dt.isoformat() if start_dt else "",
        "end_utc": end_dt.isoformat() if end_dt else "",
    }



def ensure_event_utc_fields(ev: dict) -> None:
    normalized = normalize_calendar_event(ev)
    ev.clear()
    ev.update(normalized)
