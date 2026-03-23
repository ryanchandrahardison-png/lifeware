from datetime import datetime, date, time
from zoneinfo import ZoneInfo

NY_TZ = ZoneInfo("America/New_York")
UTC_TZ = ZoneInfo("UTC")

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


def parse_event_dt_utc(value):
    return parse_dt_any(value)


def utc_to_ny(dt_utc: datetime | None) -> datetime | None:
    if dt_utc is None:
        return None
    return dt_utc.astimezone(NY_TZ)


def local_ny_date_from_utc(dt_utc: datetime | None) -> date | None:
    local = utc_to_ny(dt_utc)
    return local.date() if local else None


def format_ny_time(dt_utc: datetime | None) -> str:
    local = utc_to_ny(dt_utc)
    if local is None:
        return ""
    return local.strftime("%I:%M %p")


def now_utc() -> datetime:
    return datetime.now(UTC_TZ)


def today_ny() -> date:
    return datetime.now(NY_TZ).date()


def now_ny() -> datetime:
    return datetime.now(NY_TZ)


def is_utc_dt_today_ny(dt_utc: datetime | None, *, today: date | None = None) -> bool:
    if dt_utc is None:
        return False
    return local_ny_date_from_utc(dt_utc) == (today or today_ny())

def ensure_event_utc_fields(ev):
    if "start_utc" not in ev or not ev.get("start_utc"):
        dt = parse_dt_any(ev.get("start", ""))
        if dt:
            ev["start_utc"] = dt.isoformat()

    if "end_utc" not in ev or not ev.get("end_utc"):
        dt = parse_dt_any(ev.get("end", ""))
        if dt:
            ev["end_utc"] = dt.isoformat()

    ev.setdefault("start_utc", "")
    ev.setdefault("end_utc", "")

def local_to_utc_iso(d, t):
    dt_local = datetime.combine(d, t).replace(tzinfo=NY_TZ)
    return dt_local.astimezone(UTC_TZ).isoformat()

def utc_to_local_parts(dt):
    dt_local = dt.astimezone(NY_TZ)
    return dt_local.date(), dt_local.time().replace(second=0, microsecond=0)
