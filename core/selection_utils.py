from __future__ import annotations

from typing import Any


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
