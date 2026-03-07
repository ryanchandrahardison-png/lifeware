from datetime import date

import pandas as pd
import streamlit as st
from core.state import init_state
from core.layout import sidebar_file_controls
from core.entities import parse_date_only

st.set_page_config(page_title="Delegations", layout="wide")
init_state()
sidebar_file_controls()

st.sidebar.markdown("---")
st.sidebar.page_link("app.py", label="Home", icon="🏠")
st.sidebar.page_link("pages/calendarList.py", label="Calendar", icon="📅")
st.sidebar.page_link("pages/actions.py", label="Actions", icon="✅")
st.sidebar.page_link("pages/delegations.py", label="Delegations", icon="🤝")
st.sidebar.page_link("pages/projects.py", label="Projects", icon="📁")
st.sidebar.page_link("pages/routines.py", label="Routines", icon="🔁")

st.title("🤝 Delegations")
st.caption("Select a row to view or edit delegation details.")

if st.button("New Delegation"):
    st.session_state.delegation_view_id = None
    st.switch_page("pages/delegationItem.py")

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


def render_delegation_table(rows, row_ids, key_suffix):
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
    selected_rows = selection.selection.get("rows", []) if selection else []
    if selected_rows:
        st.session_state.delegation_view_id = row_ids[selected_rows[0]]
        st.switch_page("pages/delegationItem.py")


items = st.session_state.data.get("delegations", {})
today = date.today()
past_due = []
upcoming = []
floating = []

for item_id, record in items.items():
    if record.get("project_id") and not record.get("is_active_global", True):
        continue

    follow_up_date = parse_date_only(record.get("follow_up_date"))
    row = {
        "Title": record.get("title", "Untitled"),
        "Project": "Project" if record.get("project_id") else "",
        "Status": record.get("status", ""),
        "Follow Up": follow_up_date.isoformat() if follow_up_date else "",
    }

    if follow_up_date is None:
        floating.append((item_id, row))
    elif follow_up_date < today:
        past_due.append((item_id, row))
    else:
        upcoming.append((item_id, row))

sections = [
    ("Past Due", sorted(past_due, key=lambda item: (item[1]["Follow Up"], item[1]["Title"])), "delegations_past_due"),
    ("Upcoming", sorted(upcoming, key=lambda item: (item[1]["Follow Up"], item[1]["Title"])), "delegations_upcoming"),
    ("Floating", sorted(floating, key=lambda item: item[1]["Title"]), "delegations_floating"),
]

rendered_any = False
for label, entries, key_suffix in sections:
    if not entries:
        continue
    rendered_any = True
    st.subheader(label)
    render_delegation_table([row for _, row in entries], [item_id for item_id, _ in entries], key_suffix)

if not rendered_any:
    st.info("No delegations found in the loaded GTD file.")
