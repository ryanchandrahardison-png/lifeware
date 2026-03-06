import pandas as pd
import streamlit as st
from core.state import init_state
from core.layout import sidebar_file_controls

st.set_page_config(page_title="Actions", layout="wide")
init_state()
sidebar_file_controls()

st.sidebar.markdown("---")
st.sidebar.page_link("app.py", label="Home", icon="🏠")
st.sidebar.page_link("pages/calendarList.py", label="Calendar", icon="📅")
st.sidebar.page_link("pages/actions.py", label="Actions", icon="✅")
st.sidebar.page_link("pages/delegations.py", label="Delegations", icon="🤝")
st.sidebar.page_link("pages/routines.py", label="Routines", icon="🔁")

st.title("✅ Actions")
st.caption("Actions are currently read-only. Select a row to view details.")

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


items = st.session_state.data.get("actions", [])
rows = []
row_index = []
for idx, item in enumerate(items):
    record = _as_dict(item)
    rows.append(
        {
            "Title": _pick(record, ["title", "name", "action", "task"], "Untitled"),
            "Project": _pick(record, ["project", "area", "context"]),
            "Status": _pick(record, ["status", "state"]),
            "Due": _pick(record, ["due", "due_date", "when", "date"]),
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
        key="actions_table",
    )
    selected_rows = selection.selection.get("rows", []) if selection else []
    if selected_rows:
        st.session_state.action_view_index = row_index[selected_rows[0]]
        st.switch_page("pages/actionItem.py")
else:
    st.info("No actions found in the loaded GTD file.")
