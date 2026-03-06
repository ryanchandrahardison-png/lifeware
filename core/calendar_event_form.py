from __future__ import annotations

from datetime import date, time
import streamlit as st

from core.calendar_utils import (
    parse_dt_any,
    ensure_event_utc_fields,
    local_to_utc_iso,
    utc_to_local_parts,
)


DEFAULT_STATUS_OPTIONS = ["Scheduled", "Complete"]


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


def render_calendar_event_form(data: dict, *, event_index: int | None = None, drawer_mode: bool = False) -> None:
    calendar = data.setdefault("calendar", [])
    is_edit = event_index is not None and 0 <= event_index < len(calendar)
    event = calendar[event_index] if is_edit else None

    values = _default_form_values(event)

    title_text = "Edit Event" if is_edit else "Add Event"
    if drawer_mode:
        st.markdown(
            """
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
            """,
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

    with st.form(f"calendar_form_{'drawer' if drawer_mode else 'page'}"):
        title = st.text_input("Title", value=values["title"])

        c1, c2 = st.columns(2)
        start_date = c1.date_input("Start Date", value=values["start_date"])
        start_time = c2.time_input("Start Time", value=values["start_time"])

        c3, c4 = st.columns(2)
        end_date = c3.date_input("End Date", value=values["end_date"])
        end_time = c4.time_input("End Time", value=values["end_time"])

        description = st.text_area("Description", value=values["description"], height=180)

        status = st.selectbox(
            "Status",
            DEFAULT_STATUS_OPTIONS,
            index=0 if values["status"] != "Complete" else 1,
        )

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

    if save:
        start_utc = local_to_utc_iso(start_date, start_time)
        end_utc = local_to_utc_iso(end_date, end_time)

        if end_utc <= start_utc:
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
