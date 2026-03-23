from types import SimpleNamespace

from core.selection_utils import selected_single_row_index


def _selection(rows):
    return SimpleNamespace(selection={"rows": rows})


def test_valid_single_row_selection_index():
    idx, stale = selected_single_row_index(_selection([1]), 3)
    assert idx == 1
    assert not stale


def test_stale_or_invalid_selection_handling():
    idx, stale = selected_single_row_index(_selection([9]), 3)
    assert idx is None
    assert stale

    idx, stale = selected_single_row_index(_selection(["0"]), 3)
    assert idx is None
    assert stale
