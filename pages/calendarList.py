import streamlit as st
import pandas as pd
from datetime import datetime
from zoneinfo import ZoneInfo
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

UTC_TZ = ZoneInfo("UTC")

data = st.session_state.data
events = data.get("calendar", [])

st.title("Calendar")
st.caption("Calendar is currently read-only. Select a row to view event details.")

st.markdown(
    '''
    <style>
    [data-testid="stDataFrame"] [role="columnheader"][aria-colindex="1"],
    [data-testid="stDataFrame"] [role="gridcell"][aria-colindex="1"] {
        display: none !important;
        width: 0 !important;
        min-width: 0 !important;
        padding: 0 !important;
        border: 0 !important;
    }

    [data-testid="stDataFrame"] [role="gridcell"]:focus,
    [data-testid="stDataFrame"] [role="gridcell"]:focus-visible,
    [data-testid="stDataFrame"] [tabindex="0"]:focus,
    [data-testid="stDataFrame"] [tabindex="0"]:focus-visible,
    [data-testid="stDataFrame"] *:focus,
    [data-testid="stDataFrame"] *:focus-visible {
        outline: none !important;
        box-shadow: none !important;
        border-color: transparent !important;
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



def render_event_table(rows, row_index, key_suffix):
    if not rows:
        return

    df = pd.DataFrame(rows)

    selection = st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
        key=key_suffix,
    )

    selected_rows = selection.selection.get("rows", []) if selection else []
    if selected_rows:
        selected_pos = selected_rows[0]
        st.session_state.calendar_edit_index = row_index[selected_pos]
        st.session_state.calendar_new_mode = False
        st.switch_page("pages/calendarEvent.py")



events_sorted = sorted(enumerate(events), key=sort_key)
now_utc = datetime.now(UTC_TZ)

past_grouped = {}
upcoming_grouped = {}

for idx, ev in events_sorted:
    dt = parse_dt(ev.get("start_utc"))
    if not dt:
        continue

    target = past_grouped if dt < now_utc else upcoming_grouped
    target.setdefault(dt.date(), []).append((idx, ev, dt))


if past_grouped:
    st.subheader("Past Events")
    for day in sorted(past_grouped.keys(), reverse=True):
        st.markdown(f"**{day.strftime('%A, %B %d')}**")

        rows = []
        row_index = []

        for idx, ev, dt in past_grouped[day]:
            end_dt = parse_dt(ev.get("end_utc"))
            rows.append({
                "Title": ev.get("title", "Untitled"),
                "Start": dt.strftime("%I:%M %p"),
                "End": end_dt.strftime("%I:%M %p") if end_dt else "",
                "Status": ev.get("status", "")
            })
            row_index.append(idx)

        render_event_table(rows, row_index, f"calendar_past_{day.isoformat()}")

if upcoming_grouped:
    st.subheader("Upcoming Events")
    for day in sorted(upcoming_grouped.keys()):
        st.markdown(f"**{day.strftime('%A, %B %d')}**")

        rows = []
        row_index = []

        for idx, ev, dt in upcoming_grouped[day]:
            end_dt = parse_dt(ev.get("end_utc"))
            rows.append({
                "Title": ev.get("title", "Untitled"),
                "Start": dt.strftime("%I:%M %p"),
                "End": end_dt.strftime("%I:%M %p") if end_dt else "",
                "Status": ev.get("status", "")
            })
            row_index.append(idx)

        render_event_table(rows, row_index, f"calendar_upcoming_{day.isoformat()}")

if not past_grouped and not upcoming_grouped:
    st.info("No calendar events found in the loaded GTD file.")
