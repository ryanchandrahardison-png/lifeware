from __future__ import annotations

from datetime import date, time, datetime, timedelta
from zoneinfo import ZoneInfo

import streamlit as st

from core.calendar_utils import (
    parse_dt_any,
    ensure_event_utc_fields,
    local_to_utc_iso,
    utc_to_local_parts,
)

DEFAULT_STATUS_OPTIONS = ["Scheduled", "Complete"]
UTC_TZ = ZoneInfo("UTC")
NY_TZ = ZoneInfo("America/New_York")


def _round_up_to_next_slot(value: datetime, minutes: int = 30) -> datetime:
    floored = value.replace(second=0, microsecond=0)
    remainder = floored.minute % minutes
    if remainder == 0:
        return floored
    return floored + timedelta(minutes=(minutes - remainder))


def _time_options(step_minutes: int = 30) -> list[time]:
    options: list[time] = []
    current = datetime.combine(date.today(), time(0, 0))
    end = current + timedelta(days=1)
    while current < end:
        options.append(current.time().replace(second=0, microsecond=0))
        current += timedelta(minutes=step_minutes)
    return options


TIME_OPTIONS = _time_options(30)


def _format_time_label(value: time) -> str:
    return datetime.combine(date.today(), value).strftime("%I:%M %p")


def _time_index(options: list[time], selected: time) -> int:
    selected_clean = selected.replace(second=0, microsecond=0)
    if selected_clean in options:
        return options.index(selected_clean)

    selected_minutes = selected_clean.hour * 60 + selected_clean.minute
    for i, option in enumerate(options):
        option_minutes = option.hour * 60 + option.minute
        if option_minutes >= selected_minutes:
            return i
    return max(0, len(options) - 1)


def _default_form_values(event: dict | None) -> dict:
    values = {
        "title": "",
        "description": "",
        "status": "Scheduled",
        "start_date": date.today(),
        "start_time": time(9, 0),
        "end_date": date.today(),
        "end_time": time(9, 30),
    }

    if not isinstance(event, dict):
        return values

    ensure_event_utc_fields(event)
    values["title"] = event.get("title", "")
    values["description"] = event.get("description", "")
    values["status"] = event.get("status", "Scheduled")

    start_dt = parse_dt_any(event.get("start_utc")) or parse_dt_any(event.get("start"))
    end_dt = parse_dt_any(event.get("end_utc")) or parse_dt_any(event.get("end"))

    if start_dt:
        values["start_date"], values["start_time"] = utc_to_local_parts(start_dt)
    if end_dt:
        values["end_date"], values["end_time"] = utc_to_local_parts(end_dt)

    return values


def render_calendar_event_form(
    data: dict,
    *,
    event_index: int | None = None,
    drawer_mode: bool = False,
    read_only: bool = False,
) -> None:
    calendar = data.setdefault("calendar", [])
    is_edit = event_index is not None and 0 <= event_index < len(calendar)
    event = calendar[event_index] if is_edit else None

    values = _default_form_values(event)
    now_local = datetime.now(NY_TZ)
    min_start_dt_local = _round_up_to_next_slot(now_local, 30)

    title_text = "Event Details" if read_only else ("Edit Event" if is_edit else "Add Event")
    if drawer_mode:
        st.markdown(
            '''
            <style>
            .lw-drawer {
                background: white;
                border-left: 1px solid rgba(49, 51, 63, 0.15);
                box-shadow: -8px 0 24px rgba(15, 23, 42, 0.08);
                padding: 0.5rem 0 0 0.25rem;
                position: sticky;
                top: 0.5rem;
            }
            </style>
            ''',
            unsafe_allow_html=True,
        )
        st.markdown('<div class="lw-drawer">', unsafe_allow_html=True)
        header_cols = st.columns([6, 1])
        header_cols[0].subheader(title_text)
        if header_cols[1].button("✕", key="drawer_close", help="Close event view"):
            st.session_state.calendar_edit_index = None
            st.session_state.calendar_new_mode = False
            st.rerun()
    else:
        st.title(f"📅 {title_text}")

    if read_only and not is_edit:
        st.info("No event is selected.")
        if st.button("Back to Calendar"):
            st.switch_page("pages/calendarList.py")
        if drawer_mode:
            st.markdown("</div>", unsafe_allow_html=True)
        return

    if is_edit:
        start_default_date = values["start_date"]
        start_min_date = None
    else:
        start_default_date = max(values["start_date"], min_start_dt_local.date())
        start_min_date = min_start_dt_local.date()

    if not is_edit and start_default_date == min_start_dt_local.date():
        start_time_min = min_start_dt_local.time().replace(second=0, microsecond=0)
    else:
        start_time_min = time(0, 0)

    start_time_options = [t for t in TIME_OPTIONS if t >= start_time_min]
    if not start_time_options:
        start_time_options = [min_start_dt_local.time().replace(second=0, microsecond=0)]

    preferred_start_time = values["start_time"]
    if (
        not is_edit
        and start_default_date == min_start_dt_local.date()
        and preferred_start_time < start_time_min
    ):
        preferred_start_time = start_time_min

    start_time_index = _time_index(start_time_options, preferred_start_time)

    if is_edit:
        end_default_date = values["end_date"]
        end_min_date = None
    else:
        end_default_date = max(values["end_date"], start_default_date)
        end_min_date = start_default_date

    if not is_edit and end_default_date == start_default_date:
        selected_start_time_for_default = start_time_options[start_time_index]
        end_time_min = selected_start_time_for_default
    else:
        end_time_min = time(0, 0)

    end_time_options = [t for t in TIME_OPTIONS if t >= end_time_min]
    if not end_time_options:
        end_time_options = [end_time_min]

    preferred_end_time = values["end_time"]
    if (
        not is_edit
        and end_default_date == start_default_date
        and preferred_end_time < end_time_min
    ):
        preferred_end_time = end_time_min

    end_time_index = _time_index(end_time_options, preferred_end_time)

    with st.form(f"calendar_form_{'drawer' if drawer_mode else 'page'}"):
        title = st.text_input("Title", value=values["title"], disabled=read_only)

        c1, c2 = st.columns(2)
        start_date = c1.date_input(
            "Start Date",
            value=start_default_date,
            min_value=start_min_date,
            disabled=read_only,
        )
        start_time = c2.selectbox(
            "Start Time",
            options=start_time_options,
            index=start_time_index,
            format_func=_format_time_label,
            disabled=read_only,
        )

        c3, c4 = st.columns(2)
        end_date = c3.date_input(
            "End Date",
            value=end_default_date,
            min_value=end_min_date,
            disabled=read_only,
        )
        end_time = c4.selectbox(
            "End Time",
            options=end_time_options,
            index=end_time_index,
            format_func=_format_time_label,
            disabled=read_only,
        )

        description = st.text_area(
            "Description",
            value=values["description"],
            height=180,
            disabled=read_only,
        )

        status = st.selectbox(
            "Status",
            DEFAULT_STATUS_OPTIONS,
            index=0 if values["status"] != "Complete" else 1,
            disabled=read_only,
        )

        if read_only:
            back_label = "Close" if drawer_mode else "Back to Calendar"
            back = st.form_submit_button(back_label)
            save = False
            delete = False
            confirm_delete = False
        else:
            confirm_delete = st.checkbox("Confirm deletion") if is_edit else False
            action_cols = st.columns(3)
            save = action_cols[0].form_submit_button("Save Changes" if is_edit else "Create Event")
            delete = action_cols[1].form_submit_button("Delete Event", disabled=not is_edit)
            back_label = "Close" if drawer_mode else "Back to Calendar"
            back = action_cols[2].form_submit_button(back_label)

    if drawer_mode:
        st.markdown("</div>", unsafe_allow_html=True)

    if back:
        st.session_state.calendar_edit_index = None
        st.session_state.calendar_new_mode = False
        if drawer_mode:
            st.rerun()
        else:
            st.switch_page("pages/calendarList.py")
        return

    if delete and is_edit:
        if not confirm_delete:
            st.error("Confirm deletion first")
        else:
            del calendar[event_index]
            st.session_state.calendar_edit_index = None
            st.session_state.calendar_new_mode = False
            if drawer_mode:
                st.rerun()
            else:
                st.switch_page("pages/calendarList.py")
        return

    if save:
        start_utc = local_to_utc_iso(start_date, start_time)
        end_utc = local_to_utc_iso(end_date, end_time)

        start_dt = parse_dt_any(start_utc)
        end_dt = parse_dt_any(end_utc)
        now_utc = datetime.now(UTC_TZ)

        if not is_edit:
            if start_dt and start_dt < now_utc:
                st.error("Start time cannot be before the current date/time.")
                return

            if not start_dt or not end_dt or end_dt <= start_dt:
                st.error("End time must be after start time.")
                return

        clean_title = title.strip()
        if not clean_title:
            st.error("Title is required.")
            return

        payload = {
            "title": clean_title,
            "description": description.strip(),
            "status": status,
            "start_utc": start_utc,
            "end_utc": end_utc,
        }

        if is_edit:
            calendar[event_index] = payload
        else:
            calendar.append(payload)

        st.session_state.calendar_edit_index = None
        st.session_state.calendar_new_mode = False
        if drawer_mode:
            st.rerun()
        else:
            st.switch_page("pages/calendarList.py")
