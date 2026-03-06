import streamlit as st
from core.state import init_state
from core.layout import sidebar_file_controls
from core.calendar_utils import fmt_ny, parse_dt_any, ensure_event_utc_fields
from core.calendar_event_form import render_calendar_event_form

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

st.markdown(
    """
    <style>
    .lw-row-icon button {
        width: 2.5rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

if is_drawer_open:
    list_col, drawer_col = st.columns([1.8, 1.1], gap="large")
else:
    list_col = st.container()
    drawer_col = None

with list_col:
    top = st.columns([1, 9])

    if top[0].button("Add Event"):
        st.session_state.calendar_edit_index = None
        st.session_state.calendar_new_mode = True
        st.rerun()

    if not calendar:
        st.info("No calendar events.")
    else:
        header = st.columns([1, 5, 3, 3, 2])
        header[0].markdown("**View**")
        header[1].markdown("**Title**")
        header[2].markdown("**Start**")
        header[3].markdown("**End**")
        header[4].markdown("**Status**")

        sortable_events = []
        for i, ev in enumerate(calendar):
            if not isinstance(ev, dict):
                continue
            ensure_event_utc_fields(ev)
            sort_dt = parse_dt_any(ev.get("start_utc")) or parse_dt_any(ev.get("start"))
            sortable_events.append((sort_dt.isoformat() if sort_dt else "", i, ev))

        for _, i, ev in sorted(sortable_events, key=lambda item: item[0]):
            sdt = parse_dt_any(ev.get("start_utc")) or parse_dt_any(ev.get("start"))
            edt = parse_dt_any(ev.get("end_utc")) or parse_dt_any(ev.get("end"))

            start_txt = fmt_ny(sdt) if sdt else ""
            end_txt = fmt_ny(edt) if edt else ""

            row = st.columns([1, 5, 3, 3, 2])

            with row[0]:
                st.markdown('<div class="lw-row-icon">', unsafe_allow_html=True)
                if st.button("👁", key=f"view_{i}"):
                    st.session_state.calendar_edit_index = i
                    st.session_state.calendar_new_mode = False
                    st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)

            row[1].write(ev.get("title", ""))
            row[2].write(start_txt)
            row[3].write(end_txt)
            row[4].write(ev.get("status", "Scheduled"))

if drawer_col is not None:
    with drawer_col:
        selected_index = None if st.session_state.calendar_new_mode else st.session_state.calendar_edit_index
        render_calendar_event_form(
            data,
            event_index=selected_index,
            drawer_mode=True,
        )
