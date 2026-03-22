from datetime import date

import pandas as pd
import streamlit as st
from core.state import init_state
from core.layout import sidebar_file_controls
from core.navigation import render_primary_navigation
from core.entities import parse_date_only
from core.selection_utils import selected_single_row_index

st.set_page_config(page_title="Actions", layout="wide")
init_state()
sidebar_file_controls()

render_primary_navigation()

st.title("✅ Actions")
st.caption("Select a row to view or edit action details.")

if st.button("New Action"):
    st.session_state.return_to_project_on_back = False
    st.session_state.action_view_id = None
    st.switch_page("pages/actionItem.py")

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


def render_action_table(rows, row_ids, key_suffix):
    if not rows:
        return

    selection = st.dataframe(
        pd.DataFrame(rows),
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
        key=key_suffix,
    )
    selected_index, had_stale_selection = selected_single_row_index(selection, len(row_ids))
    if had_stale_selection:
        st.session_state.pop(key_suffix, None)
        return
    if selected_index is not None:
        st.session_state.return_to_project_on_back = False
        st.session_state.action_view_id = row_ids[selected_index]
        st.switch_page("pages/actionItem.py")


items = st.session_state.data.get("actions", {})
today = date.today()
past_due = []
upcoming = []
floating = []

for item_id, record in items.items():
    if record.get("project_id") and not record.get("is_active_global", True):
        continue

    due_date = parse_date_only(record.get("due_date"))
    row = {
        "Title": record.get("title", "Untitled"),
        "Project": "Project" if record.get("project_id") else "",
        "Status": record.get("status", ""),
        "Due": due_date.isoformat() if due_date else "",
    }

    if due_date is None:
        floating.append((item_id, row))
    elif due_date < today:
        past_due.append((item_id, row))
    else:
        upcoming.append((item_id, row))

sections = [
    ("Past Due", sorted(past_due, key=lambda item: (item[1]["Due"], item[1]["Title"])), "actions_past_due"),
    ("Upcoming", sorted(upcoming, key=lambda item: (item[1]["Due"], item[1]["Title"])), "actions_upcoming"),
    ("Floating", sorted(floating, key=lambda item: item[1]["Title"]), "actions_floating"),
]

rendered_any = False
for label, entries, key_suffix in sections:
    if not entries:
        continue
    rendered_any = True
    st.subheader(label)
    render_action_table([row for _, row in entries], [item_id for item_id, _ in entries], key_suffix)

if not rendered_any:
    st.info("No actions found in the loaded GTD file.")
