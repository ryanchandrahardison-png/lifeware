from datetime import date

from core.calendar_utils import is_utc_dt_today_ny, local_ny_date_from_utc, parse_event_dt_utc


def test_utc_near_midnight_maps_to_previous_ny_day():
    # 00:30 UTC is 20:30 previous day in New York (EDT on this date)
    dt_utc = parse_event_dt_utc("2026-07-15T00:30:00Z")
    assert dt_utc is not None
    assert local_ny_date_from_utc(dt_utc) == date(2026, 7, 14)


def test_today_logic_uses_same_ny_day_interpretation():
    dt_utc = parse_event_dt_utc("2026-07-15T00:30:00Z")
    assert dt_utc is not None

    assert is_utc_dt_today_ny(dt_utc, today=date(2026, 7, 14))
    assert not is_utc_dt_today_ny(dt_utc, today=date(2026, 7, 15))
