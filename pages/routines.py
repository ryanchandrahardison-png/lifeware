from datetime import date

import pandas as pd
import streamlit as st

from core.layout import sidebar_file_controls
from core.routine_service import ensure_routine_shape, reset_due_instance_if_needed, routine_due_today
from core.selection_utils import selected_single_row_index
from core.state import init_state

st.set_page_config(page_title="Routines", layout="wide")
init_state()
sidebar_file_controls()

st.sidebar.markdown("---")
st.sidebar.page_link("app.py", label="Home", icon="🏠")
st.sidebar.page_link("pages/calendarList.py", label="Calendar", icon="📅")
st.sidebar.page_link("pages/actions.py", label="Actions", icon="✅")
st.sidebar.page_link("pages/delegations.py", label="Delegations", icon="🤝")
st.sidebar.page_link("pages/projects.py", label="Projects", icon="📁")
st.sidebar.page_link("pages/routines.py", label="Routines", icon="🔁")
st.sidebar.page_link("pages/myDay.py", label="My Day", icon="☀️")

st.title("🔁 Routines")
st.caption("Select a row to view or edit routine details.")

for routine in st.session_state.data.get("routines", {}).values():
    ensure_routine_shape(routine)
    reset_due_instance_if_needed(routine, today=date.today())

if st.button("New Routine"):
    st.session_state.routine_view_id = None
    st.switch_page("pages/routineItem.py")

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
    </style>
    ''',
    unsafe_allow_html=True,
)

routines = st.session_state.data.get("routines", {})
rows: list[dict] = []
row_ids: list[str] = []
for routine_id, routine in sorted(routines.items(), key=lambda item: (item[1].get("start_time", ""), item[1].get("title", ""))):
    rows.append(
        {
            "Title": routine.get("title") or "Untitled",
            "Cadence": routine.get("cadence"),
            "Start": routine.get("start_time"),
            "Tasks": len(routine.get("tasks", [])),
            "Due Today": "Yes" if routine_due_today(routine) else "",
        }
    )
    row_ids.append(routine_id)

if not rows:
    st.info("No routines found in the loaded GTD file.")
    st.stop()

selection = st.dataframe(
    pd.DataFrame(rows),
    use_container_width=True,
    hide_index=True,
    on_select="rerun",
    selection_mode="single-row",
    key="routines_table",
)
selected_index, had_stale_selection = selected_single_row_index(selection, len(row_ids))
if had_stale_selection:
    st.session_state.pop("routines_table", None)
elif selected_index is not None:
    st.session_state.routine_view_id = row_ids[selected_index]
    st.switch_page("pages/routineItem.py")
