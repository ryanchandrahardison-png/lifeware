import streamlit as st
import pandas as pd
from core.state import init_session_state
from core.layout import render_session_sidebar
from core.calendar_utils import ensure_event_utc_fields, parse_dt_any, fmt_ny

init_session_state()
render_session_sidebar()

data = st.session_state.data

st.title("Calendar")

top = st.columns([1, 9])
if top[0].button("Add Event"):
    st.session_state.calendar_edit_index = None
    st.session_state.calendar_new_mode = True
    st.switch_page("pages/calendarEvent.py")

if not data["calendar"]:
    st.info("No calendar events.")
else:
    rows = []
    row_map = []

    for i, ev in enumerate(data["calendar"]):
        if not isinstance(ev, dict):
            continue

        ensure_event_utc_fields(ev)
        sdt = parse_dt_any(ev.get("start_utc")) or parse_dt_any(ev.get("start"))
        edt = parse_dt_any(ev.get("end_utc")) or parse_dt_any(ev.get("end"))

        rows.append(
            {
                "#": i + 1,
                "Title": ev.get("title", ""),
                "Start": fmt_ny(sdt) if sdt else "",
                "End": fmt_ny(edt) if edt else "",
                "Status": ev.get("status", "Scheduled"),
            }
        )
        row_map.append(i)

    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)

    open_cols = st.columns([2, 8])
    selected_number = open_cols[0].number_input(
        "Open row #",
        min_value=1,
        max_value=len(row_map),
        value=1,
        step=1,
    )

    if open_cols[1].button("👁️ View Event"):
        st.session_state.calendar_edit_index = row_map[selected_number - 1]
        st.session_state.calendar_new_mode = False
        st.switch_page("pages/calendarEvent.py")

with st.expander("Debug Session Data"):
    st.json(data)
