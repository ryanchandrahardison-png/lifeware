from __future__ import annotations

from datetime import datetime, time
from zoneinfo import ZoneInfo

import streamlit as st

from core.calendar_event_logic import (
    DEFAULT_STATUS_OPTIONS,
    UTC_TZ,
    build_event_payload,
    default_event_form_values,
    format_time_label,
    normalize_event_datetimes,
    round_up_to_next_slot,
    time_index,
    time_options,
    validate_event_submission,
)
from core.page_state import (
    flags_store,
    pop_reset_flag,
    prepare_widget_defaults,
    sync_editor_from_widgets,
    ui_store,
    widget_key,
)

NY_TZ = ZoneInfo("America/New_York")
TIME_OPTIONS = time_options(30)


def _close_event_form(*, namespace: str, drawer_mode: bool) -> None:
    st.session_state.event_view_id = None
    st.session_state.event_new_mode = False
    ui_store().pop(namespace, None)
    flags_store().pop(f"reset::{namespace}", None)
    if drawer_mode:
        st.rerun()
    else:
        st.switch_page("pages/calendarList.py")


def _init_editor_state(*, namespace: str, event_index: str | None, values: dict, is_edit: bool, read_only: bool) -> dict:
    editor = ui_store().get(namespace)
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
        ui_store()[namespace] = editor
    if editor.get("source_snapshot") != snapshot:
        editor.update(values)
        editor["source_snapshot"] = snapshot
        flags_store()[f"reset::{namespace}"] = True
    return editor


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

    values = default_event_form_values(event)

    namespace = f"calendar_event_editor::{'drawer' if drawer_mode else 'page'}"
    editor = _init_editor_state(namespace=namespace, event_index=event_index, values=values, is_edit=is_edit, read_only=read_only)

    now_local = datetime.now(NY_TZ)
    min_start_dt_local = round_up_to_next_slot(now_local, 30)

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
            _close_event_form(namespace=namespace, drawer_mode=True)
    else:
        st.title(f"📅 {title_text}")

    if read_only and not is_edit:
        st.info("No event is selected.")
        if st.button("Back to Calendar"):
            _close_event_form(namespace=namespace, drawer_mode=False)
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

    start_time_options = [t for t in TIME_OPTIONS if t >= start_time_min] or [start_time_min]
    preferred_start_time = start_time_value
    if not is_edit and start_default_date == min_start_dt_local.date() and preferred_start_time < start_time_min:
        preferred_start_time = start_time_min
    start_time_index_value = time_index(start_time_options, preferred_start_time)

    if is_edit:
        end_default_date = end_value
        end_min_date = None
    else:
        end_default_date = max(end_value, start_default_date)
        end_min_date = start_default_date

    if not is_edit and end_default_date == start_default_date:
        end_time_min = start_time_options[start_time_index_value]
    else:
        end_time_min = time(0, 0)

    end_time_options = [t for t in TIME_OPTIONS if t >= end_time_min] or [end_time_min]
    preferred_end_time = end_time_value
    if not is_edit and end_default_date == start_default_date and preferred_end_time < end_time_min:
        preferred_end_time = end_time_min
    end_time_index_value = time_index(end_time_options, preferred_end_time)

    fields = ["title", "description", "status", "start_date", "start_time", "end_date", "end_time", "confirm_delete"]
    prepare_widget_defaults(namespace, fields, editor, force=pop_reset_flag(namespace))

    start_time_key = widget_key(namespace, "start_time")
    end_time_key = widget_key(namespace, "end_time")
    if st.session_state.get(start_time_key) not in start_time_options:
        st.session_state[start_time_key] = start_time_options[start_time_index_value]
    if st.session_state.get(end_time_key) not in end_time_options:
        st.session_state[end_time_key] = end_time_options[end_time_index_value]

    with st.form(f"calendar_form_{'drawer' if drawer_mode else 'page'}"):
        st.text_input("Title", key=widget_key(namespace, "title"), disabled=read_only)

        c1, c2 = st.columns(2)
        start_date_kwargs = {"key": widget_key(namespace, "start_date"), "disabled": read_only}
        if start_min_date is not None:
            start_date_kwargs["min_value"] = start_min_date
        c1.date_input("Start Date", **start_date_kwargs)
        c2.selectbox(
            "Start Time",
            options=start_time_options,
            index=time_index(start_time_options, st.session_state.get(start_time_key, start_time_options[0])),
            format_func=format_time_label,
            disabled=read_only,
            key=start_time_key,
        )

        c3, c4 = st.columns(2)
        end_date_kwargs = {"key": widget_key(namespace, "end_date"), "disabled": read_only}
        if end_min_date is not None:
            end_date_kwargs["min_value"] = end_min_date
        c3.date_input("End Date", **end_date_kwargs)
        c4.selectbox(
            "End Time",
            options=end_time_options,
            index=time_index(end_time_options, st.session_state.get(end_time_key, end_time_options[0])),
            format_func=format_time_label,
            disabled=read_only,
            key=end_time_key,
        )

        st.text_area("Description", key=widget_key(namespace, "description"), height=180, disabled=read_only)

        st.selectbox(
            "Status",
            DEFAULT_STATUS_OPTIONS,
            index=0 if str(editor.get("status", "Scheduled")) != "Complete" else 1,
            disabled=read_only,
            key=widget_key(namespace, "status"),
        )

        if read_only:
            back = st.form_submit_button("Close" if drawer_mode else "Back to Calendar")
            save = False
            delete = False
            confirm_delete = False
        else:
            if is_edit:
                st.checkbox("Confirm deletion", key=widget_key(namespace, "confirm_delete"))
            else:
                st.session_state[widget_key(namespace, "confirm_delete")] = False
            action_cols = st.columns(3)
            save = action_cols[0].form_submit_button("Save Changes" if is_edit else "Create Event")
            delete = action_cols[1].form_submit_button("Delete Event", disabled=not is_edit)
            back = action_cols[2].form_submit_button("Close" if drawer_mode else "Back to Calendar")
            confirm_delete = bool(st.session_state.get(widget_key(namespace, "confirm_delete"), False))

    sync_editor_from_widgets(namespace, fields, editor)

    if drawer_mode:
        st.markdown("</div>", unsafe_allow_html=True)

    if back:
        _close_event_form(namespace=namespace, drawer_mode=drawer_mode)
        return

    if delete and is_edit:
        if not confirm_delete:
            st.error("Confirm deletion first")
        else:
            del events[event_index]
            _close_event_form(namespace=namespace, drawer_mode=drawer_mode)
        return

    if save:
        start_utc, end_utc, start_dt, end_dt = normalize_event_datetimes(editor=editor)
        title = str(editor.get("title", "") or "")
        errors = validate_event_submission(
            is_edit=is_edit,
            title=title,
            start_dt=start_dt,
            end_dt=end_dt,
            now_utc=datetime.now(UTC_TZ),
        )
        if errors:
            for error in errors:
                st.error(error)
            return

        payload = build_event_payload(
            event_id=event_index,
            is_edit=is_edit,
            title=title,
            description=str(editor.get("description", "") or ""),
            status=str(editor.get("status", "Scheduled") or "Scheduled"),
            start_utc=start_utc,
            end_utc=end_utc,
        )
        events[payload["id"]] = payload
        _close_event_form(namespace=namespace, drawer_mode=drawer_mode)
