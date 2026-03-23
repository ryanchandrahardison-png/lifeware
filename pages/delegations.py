from datetime import date

import streamlit as st
from core.layout import bootstrap_page
from core.entities import parse_date_only
from core.selection_utils import (
    inject_selection_column_hide_css,
    selectable_table_single_row,
    selected_single_row_index,
)

bootstrap_page("Delegations")

st.title("🤝 Delegations")
st.caption("Select a row to view or edit delegation details.")

if st.button("New Delegation"):
    st.session_state.return_to_project_on_back = False
    st.session_state.delegation_view_id = None
    st.switch_page("pages/delegationItem.py")

inject_selection_column_hide_css()


def render_delegation_table(rows, row_ids, key_suffix):
    if not rows:
        return

    selection = selectable_table_single_row(rows, key=key_suffix)
    selected_index, had_stale_selection = selected_single_row_index(selection, len(row_ids))
    if had_stale_selection:
        st.session_state.pop(key_suffix, None)
        return
    if selected_index is not None:
        st.session_state.return_to_project_on_back = False
        st.session_state.delegation_view_id = row_ids[selected_index]
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
