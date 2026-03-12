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
from core.entities import new_uuid

DEFAULT_STATUS_OPTIONS = ["Scheduled", "Complete"]
UTC_TZ = ZoneInfo("UTC")
NY_TZ = ZoneInfo("America/New_York")


def _ui_store() -> dict:
    st.session_state.setdefault("ui", {})
    return st.session_state.ui


def _flags_store() -> dict:
    st.session_state.setdefault("flags", {})
    return st.session_state.flags


def _widget_key(namespace: str, field: str) -> str:
    return f"{namespace}__{field}"


def _pop_reset_flag(namespace: str) -> bool:
    return bool(_flags_store().pop(f"reset::{namespace}", False))


def _prepare_widget_defaults(namespace: str, fields: list[str], editor: dict, *, force: bool = False) -> None:
    for field in fields:
        key = _widget_key(namespace, field)
        if force or key not in st.session_state:
            st.session_state[key] = editor.get(field)


def _sync_editor_from_widgets(namespace: str, fields: list[str], editor: dict) -> None:
    for field in fields:
        editor[field] = st.session_state.get(_widget_key(namespace, field))


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


def render_calendar_event_form(
    data: dict,
    *,
    event_index: str | None = None,
    drawer_mode: bool = False,
    read_only: bool = False,
) -> None:
    events = data.setdefault("events", {})
    is_edit = event_index is not None and event_index in events
    event = events.get(event_index) if is_edit else None

    values = _default_form_values(event)

    namespace = f"calendar_event_editor::{ 'drawer' if drawer_mode else 'page' }"
    editor = _ui_store().get(namespace)
    snapshot = (
        event_index,
        values["title"],
        values["description"],
        values["status"],
        values["start_date"].isoformat(),
        values["start_time"].isoformat(),
        values["end_date"].isoformat(),
        values["end_time"].isoformat(),
        bool(is_edit),
        bool(read_only),
    )
    if not isinstance(editor, dict):
        editor = {}
        _ui_store()[namespace] = editor
    if editor.get("source_snapshot") != snapshot:
        editor.update(values)
        editor["source_snapshot"] = snapshot
        _flags_store()[f"reset::{namespace}"] = True

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
            st.session_state.event_view_id = None
            st.session_state.event_new_mode = False
            _ui_store().pop(namespace, None)
            _flags_store().pop(f"reset::{namespace}", None)
            st.rerun()
    else:
        st.title(f"📅 {title_text}")

    if read_only and not is_edit:
        st.info("No event is selected.")
        if st.button("Back to Calendar"):
            _ui_store().pop(namespace, None)
            _flags_store().pop(f"reset::{namespace}", None)
            st.switch_page("pages/calendarList.py")
        if drawer_mode:
            st.markdown("</div>", unsafe_allow_html=True)
        return

    start_value = editor.get("start_date", values["start_date"])
    start_time_value = editor.get("start_time", values["start_time"])
    end_value = editor.get("end_date", values["end_date"])
    end_time_value = editor.get("end_time", values["end_time"])

    if is_edit:
        start_default_date = start_value
        start_min_date = None
    else:
        start_default_date = max(start_value, min_start_dt_local.date())
        start_min_date = min_start_dt_local.date()

    if not is_edit and start_default_date == min_start_dt_local.date():
        start_time_min = min_start_dt_local.time().replace(second=0, microsecond=0)
    else:
        start_time_min = time(0, 0)

    start_time_options = [t for t in TIME_OPTIONS if t >= start_time_min]
    if not start_time_options:
        start_time_options = [min_start_dt_local.time().replace(second=0, microsecond=0)]

    preferred_start_time = start_time_value
    if (
        not is_edit
        and start_default_date == min_start_dt_local.date()
        and preferred_start_time < start_time_min
    ):
        preferred_start_time = start_time_min

    start_time_index = _time_index(start_time_options, preferred_start_time)

    if is_edit:
        end_default_date = end_value
        end_min_date = None
    else:
        end_default_date = max(end_value, start_default_date)
        end_min_date = start_default_date

    if not is_edit and end_default_date == start_default_date:
        selected_start_time_for_default = start_time_options[start_time_index]
        end_time_min = selected_start_time_for_default
    else:
        end_time_min = time(0, 0)

    end_time_options = [t for t in TIME_OPTIONS if t >= end_time_min]
    if not end_time_options:
        end_time_options = [end_time_min]

    preferred_end_time = end_time_value
    if (
        not is_edit
        and end_default_date == start_default_date
        and preferred_end_time < end_time_min
    ):
        preferred_end_time = end_time_min

    end_time_index = _time_index(end_time_options, preferred_end_time)

    fields = ["title", "description", "status", "start_date", "start_time", "end_date", "end_time", "confirm_delete"]
    _prepare_widget_defaults(namespace, fields, editor, force=_pop_reset_flag(namespace))

    # Ensure time key values are valid for current option sets before widget render.
    start_time_key = _widget_key(namespace, "start_time")
    end_time_key = _widget_key(namespace, "end_time")
    if st.session_state.get(start_time_key) not in start_time_options:
        st.session_state[start_time_key] = start_time_options[start_time_index]
    if st.session_state.get(end_time_key) not in end_time_options:
        st.session_state[end_time_key] = end_time_options[end_time_index]

    with st.form(f"calendar_form_{'drawer' if drawer_mode else 'page'}"):
        st.text_input("Title", key=_widget_key(namespace, "title"), disabled=read_only)

        c1, c2 = st.columns(2)
        start_date_kwargs = {
            "key": _widget_key(namespace, "start_date"),
            "disabled": read_only,
        }
        if start_min_date is not None:
            start_date_kwargs["min_value"] = start_min_date
        c1.date_input("Start Date", **start_date_kwargs)
        c2.selectbox(
            "Start Time",
            options=start_time_options,
            index=_time_index(start_time_options, st.session_state.get(start_time_key, start_time_options[0])),
            format_func=_format_time_label,
            disabled=read_only,
            key=start_time_key,
        )

        c3, c4 = st.columns(2)
        end_date_kwargs = {
            "key": _widget_key(namespace, "end_date"),
            "disabled": read_only,
        }
        if end_min_date is not None:
            end_date_kwargs["min_value"] = end_min_date
        c3.date_input("End Date", **end_date_kwargs)
        c4.selectbox(
            "End Time",
            options=end_time_options,
            index=_time_index(end_time_options, st.session_state.get(end_time_key, end_time_options[0])),
            format_func=_format_time_label,
            disabled=read_only,
            key=end_time_key,
        )

        st.text_area(
            "Description",
            key=_widget_key(namespace, "description"),
            height=180,
            disabled=read_only,
        )

        st.selectbox(
            "Status",
            DEFAULT_STATUS_OPTIONS,
            index=0 if str(editor.get("status", "Scheduled")) != "Complete" else 1,
            disabled=read_only,
            key=_widget_key(namespace, "status"),
        )

        if read_only:
            back_label = "Close" if drawer_mode else "Back to Calendar"
            back = st.form_submit_button(back_label)
            save = False
            delete = False
            confirm_delete = False
        else:
            if is_edit:
                st.checkbox("Confirm deletion", key=_widget_key(namespace, "confirm_delete"))
            else:
                st.session_state[_widget_key(namespace, "confirm_delete")] = False
            action_cols = st.columns(3)
            save = action_cols[0].form_submit_button("Save Changes" if is_edit else "Create Event")
            delete = action_cols[1].form_submit_button("Delete Event", disabled=not is_edit)
            back_label = "Close" if drawer_mode else "Back to Calendar"
            back = action_cols[2].form_submit_button(back_label)
            confirm_delete = bool(st.session_state.get(_widget_key(namespace, "confirm_delete"), False))

    _sync_editor_from_widgets(namespace, fields, editor)

    if drawer_mode:
        st.markdown("</div>", unsafe_allow_html=True)

    if back:
        st.session_state.event_view_id = None
        st.session_state.event_new_mode = False
        _ui_store().pop(namespace, None)
        _flags_store().pop(f"reset::{namespace}", None)
        if drawer_mode:
            st.rerun()
        else:
            st.switch_page("pages/calendarList.py")
        return

    if delete and is_edit:
        if not confirm_delete:
            st.error("Confirm deletion first")
        else:
            del events[event_index]
            st.session_state.event_view_id = None
            st.session_state.event_new_mode = False
            _ui_store().pop(namespace, None)
            _flags_store().pop(f"reset::{namespace}", None)
            if drawer_mode:
                st.rerun()
            else:
                st.switch_page("pages/calendarList.py")
        return

    if save:
        start_date = editor.get("start_date")
        start_time = editor.get("start_time")
        end_date = editor.get("end_date")
        end_time = editor.get("end_time")
        title = str(editor.get("title", "") or "")
        description = str(editor.get("description", "") or "")
        status = str(editor.get("status", "Scheduled") or "Scheduled")

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
            "id": event_index if is_edit else new_uuid(),
            "title": clean_title,
            "details": description.strip(),
            "status": status,
            "start_utc": start_utc,
            "end_utc": end_utc,
        }

        events[payload["id"]] = payload

        st.session_state.event_view_id = None
        st.session_state.event_new_mode = False
        _ui_store().pop(namespace, None)
        _flags_store().pop(f"reset::{namespace}", None)
        if drawer_mode:
            st.rerun()
        else:
            st.switch_page("pages/calendarList.py")
