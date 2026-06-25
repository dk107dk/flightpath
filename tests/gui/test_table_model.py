"""
Unit tests for TableModel (flightpath/widgets/table_model.py).

TableModel subclasses QAbstractTableModel so a QApplication is required.
Tests focus on the pure data-manipulation logic — row/column counts,
insertions, removals, data access — without rendering any widgets.

Run with:
  QT_QPA_PLATFORM=offscreen poetry run python -m pytest tests/gui/test_table_model.py -v
"""

import pytest

from flightpath.widgets.table_model import TableModel


# ---------------------------------------------------------------------------
# Qt application
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True, scope="module")
def _require_qapp(qapp):
    pass


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _model(*rows) -> TableModel:
    """Build a TableModel from the given row lists."""
    return TableModel(data=list(rows))


# ---------------------------------------------------------------------------
# rowCount / columnCount
# ---------------------------------------------------------------------------


def test_row_count_empty_model():
    assert TableModel(data=[]).rowCount() == 0


def test_row_count_populated():
    m = _model(["a", "b"], ["c", "d"], ["e", "f"])
    assert m.rowCount() == 3


def test_column_count_empty_model():
    assert TableModel(data=[]).columnCount() == 0


def test_column_count_uniform_rows():
    m = _model(["a", "b", "c"], ["d", "e", "f"])
    assert m.columnCount() == 3


def test_column_count_ragged_rows_returns_max():
    """columnCount is the width of the widest row."""
    m = _model(["a"], ["b", "c", "d"], ["e", "f"])
    assert m.columnCount() == 3


# ---------------------------------------------------------------------------
# data_row
# ---------------------------------------------------------------------------


def test_data_row_returns_correct_row():
    m = _model(["x", "y"], ["p", "q"])
    assert m.data_row(1) == ["p", "q"]


def test_data_row_first_row():
    m = _model(["first", "row"], ["second", "row"])
    assert m.data_row(0) == ["first", "row"]


def test_data_row_none_index_raises():
    m = _model(["a", "b"])
    with pytest.raises(ValueError, match="Index cannot be None"):
        m.data_row(None)


def test_data_row_index_too_large_raises():
    m = _model(["a", "b"])
    with pytest.raises(ValueError, match="too large"):
        m.data_row(99)


# ---------------------------------------------------------------------------
# insertRows
# ---------------------------------------------------------------------------


def test_insert_rows_increases_row_count():
    m = _model(["a", "b"], ["c", "d"])
    m.insertRows(0)
    assert m.rowCount() == 3


def test_insert_rows_at_index_zero_shifts_existing():
    m = _model(["a", "b"])
    m.insertRows(0, new_row_data=["x", "y"])
    assert m.data_row(0) == ["x", "y"]
    assert m.data_row(1) == ["a", "b"]


def test_insert_rows_at_end_appends():
    m = _model(["a", "b"])
    m.insertRows(1, new_row_data=["z", "z"])
    assert m.data_row(1) == ["z", "z"]
    assert m.rowCount() == 2


def test_insert_rows_no_data_creates_empty_row():
    """When new_row_data is None, a row of empty strings is inserted."""
    m = _model(["a", "b", "c"])
    m.insertRows(0)
    new_row = m.data_row(0)
    assert new_row == ["", "", ""]


# ---------------------------------------------------------------------------
# insertColumns
# ---------------------------------------------------------------------------


def test_insert_columns_increases_column_count():
    m = _model(["a", "b"], ["c", "d"])
    m.insertColumns(0)
    assert m.columnCount() == 3


def test_insert_columns_at_zero_prepends_empty_cell():
    m = _model(["a", "b"])
    m.insertColumns(0)
    assert m.data_row(0) == ["", "a", "b"]


def test_insert_columns_all_rows_get_new_cell():
    m = _model(["a", "b"], ["c", "d"])
    m.insertColumns(1)
    assert m.data_row(0)[1] == ""
    assert m.data_row(1)[1] == ""
    assert m.columnCount() == 3


# ---------------------------------------------------------------------------
# remove_rows
# ---------------------------------------------------------------------------


def test_remove_rows_decreases_row_count():
    m = _model(["a"], ["b"], ["c"])
    result = m.remove_rows(1, 1)
    assert result is True
    assert m.rowCount() == 2


def test_remove_rows_removes_correct_row():
    m = _model(["keep"], ["delete"], ["keep2"])
    m.remove_rows(1, 1)
    assert m.data_row(0) == ["keep"]
    assert m.data_row(1) == ["keep2"]


def test_remove_rows_negative_index_returns_false():
    m = _model(["a"], ["b"])
    assert m.remove_rows(-1, 1) is False


def test_remove_rows_out_of_range_returns_false():
    m = _model(["a"], ["b"])
    assert m.remove_rows(5, 1) is False


def test_remove_rows_count_exceeds_remaining_returns_false():
    m = _model(["a"], ["b"])
    assert m.remove_rows(1, 5) is False


# ---------------------------------------------------------------------------
# remove_columns
# ---------------------------------------------------------------------------


def test_remove_columns_decreases_column_count():
    m = _model(["a", "b", "c"], ["d", "e", "f"])
    result = m.remove_columns(1, 1)
    assert result is True
    assert m.columnCount() == 2


def test_remove_columns_removes_correct_column():
    m = _model(["a", "b", "c"])
    m.remove_columns(1, 1)
    assert m.data_row(0) == ["a", "c"]


def test_remove_columns_negative_index_returns_false():
    m = _model(["a", "b"])
    assert m.remove_columns(-1, 1) is False


def test_remove_columns_out_of_range_returns_false():
    m = _model(["a", "b"])
    assert m.remove_columns(5, 1) is False
