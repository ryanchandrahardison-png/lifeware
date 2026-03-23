from __future__ import annotations

from typing import Any

import pandas as pd
import streamlit as st


SELECTION_COLUMN_HIDE_CSS = """
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
"""


def inject_selection_column_hide_css() -> None:
    st.markdown(SELECTION_COLUMN_HIDE_CSS, unsafe_allow_html=True)


def selected_single_row_index(selection: Any, row_count: int) -> tuple[int | None, bool]:
    """Return selected row index for single-row dataframe selections.

    Returns `(index, had_stale_selection)`.
    - `index` is `None` when no valid selection exists.
    - `had_stale_selection` is `True` when a selection exists but is invalid/out of range.
    """

    if row_count <= 0 or selection is None:
        return None, False

    rows: list[int] = []
    try:
        rows = selection.selection.get("rows", []) or []
    except Exception:
        return None, False

    if not rows:
        return None, False

    selected = rows[0]
    if not isinstance(selected, int):
        return None, True

    if selected < 0 or selected >= row_count:
        return None, True

    return selected, False


def selectable_table_single_row(rows: list[dict[str, Any]], *, key: str) -> Any:
    return st.dataframe(
        pd.DataFrame(rows),
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
        key=key,
    )
