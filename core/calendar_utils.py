
from datetime import datetime
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
        return None

def ensure_event_utc_fields(ev):
    ev.setdefault("start_utc","")
    ev.setdefault("end_utc","")
