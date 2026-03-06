import streamlit as st

from core.calendar_event_form import render_calendar_event_form
from core.calendar_utils import NY_TZ, parse_dt_any
from core.layout import sidebar_file_controls
from core.state import init_state


st.set_page_config(page_title="Calendar", layout="wide")
init_state()
sidebar_file_controls()

st.sidebar.markdown("---")
st.sidebar.page_link("app.py", label="Home", icon="🏠")
st.sidebar.page_link("pages/calendarList.py", label="Calendar", icon="📅")
st.sidebar.page_link("pages/actions.py", label="Actions", icon="✅")
st.sidebar.page_link("pages/delegations.py", label="Delegations", icon="🤝")
st.sidebar.page_link("pages/routines.py", label="Routines", icon="🔁")


data = st.session_state.data
calendar = data.setdefault("calendar", [])

is_drawer_open = (
    st.session_state.calendar_new_mode
    or st.session_state.calendar_edit_index is not None
)

st.title("📅 Calendar")

if is_drawer_open:
    list_col, drawer_col = st.columns([1.8, 1.1], gap="large")
else:
    list_col = st.container()
    drawer_col = None


def _sort_key(event: dict) -> tuple:
    start_dt = parse_dt_any(event.get("start_utc")) or parse_dt_any(event.get("start"))
    if start_dt:
        return (0, start_dt.isoformat(), event.get("title", "").lower())
    return (1, "", event.get("title", "").lower())


def _grouped_calendar_rows() -> list[tuple[str, list[dict]]]:
    grouped: dict[str, list[dict]] = {}

    indexed_events = [(idx, ev) for idx, ev in enumerate(calendar) if isinstance(ev, dict)]
    for source_index, event in sorted(indexed_events, key=lambda item: _sort_key(item[1])):
        start_dt = parse_dt_any(event.get("start_utc")) or parse_dt_any(event.get("start"))
        end_dt = parse_dt_any(event.get("end_utc")) or parse_dt_any(event.get("end"))

        if start_dt:
            local_start = start_dt.astimezone(NY_TZ)
            day_key = local_start.date().isoformat()
            day_label = local_start.strftime("%A, %B %d, %Y")
            start_txt = local_start.strftime("%I:%M %p").lstrip("0")
        else:
            day_key = "no_date"
            day_label = "No Date"
            start_txt = ""

        end_txt = ""
        if end_dt:
            end_txt = end_dt.astimezone(NY_TZ).strftime("%I:%M %p").lstrip("0")

        grouped.setdefault(day_key, []).append(
            {
                "source_index": source_index,
                "day_label": day_label,
                "Title": event.get("title", ""),
                "Start": start_txt,
                "End": end_txt,
                "Status": event.get("status", "Scheduled"),
            }
        )

    ordered_groups = []
    for day_key in sorted(grouped.keys(), key=lambda value: (value == "no_date", value)):
        ordered_groups.append((grouped[day_key][0]["day_label"], grouped[day_key]))
    return ordered_groups


def _open_event(source_index: int) -> None:
    st.session_state.calendar_edit_index = source_index
    st.session_state.calendar_new_mode = False
    st.rerun()


with list_col:
    if st.button("Add Event"):
        st.session_state.calendar_edit_index = None
        st.session_state.calendar_new_mode = True
        st.rerun()

    if not calendar:
        st.info("No calendar events.")
    else:
        for group_num, (day_label, rows) in enumerate(_grouped_calendar_rows()):
            st.subheader(day_label)

            header_cols = st.columns([4, 1.2, 1.2, 1.2], gap="small")
            header_cols[0].markdown("**Title**")
            header_cols[1].markdown("**Start**")
            header_cols[2].markdown("**End**")
            header_cols[3].markdown("**Status**")

            for row_num, row in enumerate(rows):
                row_cols = st.columns([4, 1.2, 1.2, 1.2], gap="small")
                for col, field in zip(row_cols, ["Title", "Start", "End", "Status"]):
                    if col.button(
                        row[field] or " ",
                        key=f"calendar_row_{group_num}_{row_num}_{field.lower()}",
                        use_container_width=True,
                    ):
                        _open_event(row["source_index"])

            st.markdown("")

if drawer_col is not None:
    with drawer_col:
        selected_index = None if st.session_state.calendar_new_mode else st.session_state.calendar_edit_index
        render_calendar_event_form(
            data,
            event_index=selected_index,
            drawer_mode=True,
        )
