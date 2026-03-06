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
st.caption("Delegations are Select a row to view or edit details.")

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


def _as_dict(item):
    return item if isinstance(item, dict) else {"title": str(item)}



def _pick(record, keys, default=""):
    for key in keys:
        value = record.get(key)
        if value not in (None, ""):
            return value
    return default


items = st.session_state.data.get("delegations", [])
rows = []
row_index = []
for idx, item in enumerate(items):
    record = _as_dict(item)
    rows.append(
        {
            "Delegation": _pick(record, ["title", "name", "task", "item"], "Untitled"),
            "Owner": _pick(record, ["owner", "person", "delegate", "assigned_to"]),
            "Status": _pick(record, ["status", "state"]),
            "Follow Up": _pick(record, ["follow_up", "due", "due_date", "when", "date"]),
        }
    )
    row_index.append(idx)

if rows:
    selection = st.dataframe(
        pd.DataFrame(rows),
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
        key="delegations_table",
    )
    selected_rows = selection.selection.get("rows", []) if selection else []
    if selected_rows:
        st.session_state.delegation_view_index = row_index[selected_rows[0]]
        st.switch_page("pages/delegationItem.py")
else:
    st.info("No delegations found in the loaded GTD file.")
