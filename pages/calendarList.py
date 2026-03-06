import streamlit as st
import pandas as pd
from datetime import datetime
from core.state import init_state
from core.layout import sidebar_file_controls

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
events = data.get("calendar", [])

st.title("Calendar")

# Streamlit adds a selection column for selectable dataframes.
# Hide that column so the table keeps a clean Asana-style look while
# preserving true row-click selection behavior.
st.markdown(
    '''
    <style>
    [data-testid="stDataFrame"] [role="gridcell"][aria-colindex="1"],
    [data-testid="stDataFrame"] [role="columnheader"][aria-colindex="1"] {
        display: none !important;
    }
    </style>
    ''',
    unsafe_allow_html=True,
)


def parse_dt(value):
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def sort_key(item):
    idx, ev = item
    dt = parse_dt(ev.get("start_utc") or "")
    has_dt = dt is not None
    sortable = dt.isoformat() if dt else ""
    return (0 if has_dt else 1, sortable, idx)


events_sorted = sorted(enumerate(events), key=sort_key)

grouped = {}
for idx, ev in events_sorted:
    dt = parse_dt(ev.get("start_utc"))
    if not dt:
        continue
    grouped.setdefault(dt.date(), []).append((idx, ev, dt))


for day in sorted(grouped.keys()):
    st.subheader(day.strftime("%A, %B %d"))

    rows = []
    row_index = []

    for idx, ev, dt in grouped[day]:
        end_dt = parse_dt(ev.get("end_utc"))
        rows.append({
            "Title": ev.get("title", "Untitled"),
            "Start": dt.strftime("%I:%M %p"),
            "End": end_dt.strftime("%I:%M %p") if end_dt else "",
            "Status": ev.get("status", "")
        })
        row_index.append(idx)

    if rows:
        df = pd.DataFrame(rows)

        selection = st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            on_select="rerun",
            selection_mode="single-row",
            key=f"calendar_day_{day.isoformat()}",
        )

        selected_rows = selection.selection.get("rows", []) if selection else []
        if selected_rows:
            selected_pos = selected_rows[0]
            st.session_state.calendar_edit_index = row_index[selected_pos]
            st.session_state.calendar_new_mode = False
            st.switch_page("pages/calendarEvent.py")

st.divider()

if st.button("Add Event"):
    st.session_state.calendar_new_mode = True
    st.session_state.calendar_edit_index = None
    st.switch_page("pages/calendarEvent.py")
