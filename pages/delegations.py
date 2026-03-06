from datetime import date

import pandas as pd
import streamlit as st
from core.state import init_state
from core.layout import sidebar_file_controls

st.set_page_config(page_title="Delegations", layout="wide")
init_state()
sidebar_file_controls()

st.sidebar.markdown("---")
st.sidebar.page_link("app.py", label="Home", icon="🏠")
st.sidebar.page_link("pages/calendarList.py", label="Calendar", icon="📅")
st.sidebar.page_link("pages/actions.py", label="Actions", icon="✅")
st.sidebar.page_link("pages/delegations.py", label="Delegations", icon="🤝")
st.sidebar.page_link("pages/routines.py", label="Routines", icon="🔁")

st.title("🤝 Delegations")
st.caption("Select a row to view or edit delegation details.")

if st.button("New Delegation"):
    st.session_state.delegation_view_index = None
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

FOLLOW_UP_FIELD_CANDIDATES = ["follow_up_date", "follow_up", "due_date", "due", "when", "date"]


def _as_dict(item):
    return item if isinstance(item, dict) else {"title": str(item)}


def _pick(record, keys, default=""):
    for key in keys:
        value = record.get(key)
        if value not in (None, ""):
            return value
    return default


def _parse_date_only(value):
    if value in (None, ""):
        return None
    try:
        text = str(value).strip()
        if "T" in text:
            text = text.split("T", 1)[0]
        return date.fromisoformat(text)
    except Exception:
        return None


def render_delegation_table(rows, row_index, key_suffix):
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
        st.session_state.delegation_view_index = row_index[selected_rows[0]]
        st.switch_page("pages/delegationItem.py")


items = st.session_state.data.get("delegations", [])
today = date.today()
past_due = []
upcoming = []
floating = []

for idx, item in enumerate(items):
    record = _as_dict(item)
    follow_up_value = _pick(record, FOLLOW_UP_FIELD_CANDIDATES)
    follow_up_date = _parse_date_only(follow_up_value)
    row = {
        "Delegation": _pick(record, ["title", "name", "task", "item"], "Untitled"),
        "Owner": _pick(record, ["owner", "person", "delegate", "assigned_to"]),
        "Status": _pick(record, ["status", "state"]),
        "Follow Up": follow_up_date.isoformat() if follow_up_date else "",
    }

    if follow_up_date is None:
        floating.append((idx, row))
    elif follow_up_date < today:
        past_due.append((idx, row))
    else:
        upcoming.append((idx, row))

sections = [
    ("Past Due", sorted(past_due, key=lambda item: (item[1]["Follow Up"], item[1]["Delegation"])), "delegations_past_due"),
    ("Upcoming", sorted(upcoming, key=lambda item: (item[1]["Follow Up"], item[1]["Delegation"])), "delegations_upcoming"),
    ("Floating", sorted(floating, key=lambda item: item[1]["Delegation"]), "delegations_floating"),
]

rendered_any = False
for label, entries, key_suffix in sections:
    if not entries:
        continue
    rendered_any = True
    st.subheader(label)
    render_delegation_table([row for _, row in entries], [idx for idx, _ in entries], key_suffix)

if not rendered_any:
    st.info("No delegations found in the loaded GTD file.")
