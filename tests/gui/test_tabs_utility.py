"""
Unit tests for TabsUtility (flightpath/util/tabs_utility.py).

Covers every public method:
  find_tab           — (index, widget) or None, by objectName
  tab_index          — index or ValueError, by widget identity
  tab_index_if       — index or -1, by widget identity
  tab_index_by_name  — index or ValueError, by objectName
  tab_index_by_name_if — index or -1, by objectName
  tabs               — list of all widgets in order
  has_type           — True/False, by isinstance check
  select_tab         — sets currentIndex; accepts int or QWidget
  select_tab_widget  — sets currentIndex by widget; returns bool

TabsUtility uses Qt types (QTabWidget, QWidget), so a QApplication is
required.  The module-level autouse fixture pulls in pytest-qt's session
QApplication.

Known bug pinned here:
  select_tab(tabs, i) has a broken f-string: the ValueError message is
  literally 'No such tab: {i}' rather than interpolating the index value.

Run with:
  QT_QPA_PLATFORM=offscreen poetry run python -m pytest tests/gui/test_tabs_utility.py -v
"""

import pytest
from PySide6.QtWidgets import QTabWidget, QWidget

from flightpath.util.tabs_utility import TabsUtility as taut


# ---------------------------------------------------------------------------
# Qt application — required for QWidget
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True, scope="module")
def _require_qapp(qapp):
    pass


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _tw(*names: str) -> QTabWidget:
    """Return a QTabWidget with one plain QWidget per name, objectName set."""
    tw = QTabWidget()
    for name in names:
        w = QWidget()
        w.setObjectName(name)
        tw.addTab(w, name)
    return tw


# ---------------------------------------------------------------------------
# find_tab
# ---------------------------------------------------------------------------


def test_find_tab_returns_index_and_widget():
    tw = _tw("alpha", "beta", "gamma")
    result = taut.find_tab(tw, "beta")
    assert result is not None
    idx, widget = result
    assert idx == 1
    assert widget.objectName() == "beta"


def test_find_tab_first_tab():
    tw = _tw("alpha", "beta", "gamma")
    result = taut.find_tab(tw, "alpha")
    assert result[0] == 0


def test_find_tab_last_tab():
    tw = _tw("alpha", "beta", "gamma")
    result = taut.find_tab(tw, "gamma")
    assert result[0] == 2


def test_find_tab_not_found_returns_none():
    tw = _tw("alpha", "beta")
    assert taut.find_tab(tw, "missing") is None


def test_find_tab_empty_tab_widget_returns_none():
    assert taut.find_tab(QTabWidget(), "anything") is None


def test_find_tab_widget_in_result_is_the_actual_widget():
    """The returned widget must be the same object (identity) as tabs.widget(i)."""
    tw = _tw("alpha", "beta")
    result = taut.find_tab(tw, "alpha")
    assert result[1] is tw.widget(0)


# ---------------------------------------------------------------------------
# tab_index
# ---------------------------------------------------------------------------


def test_tab_index_returns_correct_index():
    tw = _tw("alpha", "beta", "gamma")
    assert taut.tab_index(tw, tw.widget(1)) == 1


def test_tab_index_first_widget():
    tw = _tw("alpha", "beta")
    assert taut.tab_index(tw, tw.widget(0)) == 0


def test_tab_index_not_found_raises():
    tw = _tw("alpha")
    orphan = QWidget()
    with pytest.raises(ValueError, match="No such tab"):
        taut.tab_index(tw, orphan)


def test_tab_index_empty_tab_widget_raises():
    with pytest.raises(ValueError):
        taut.tab_index(QTabWidget(), QWidget())


# ---------------------------------------------------------------------------
# tab_index_if
# ---------------------------------------------------------------------------


def test_tab_index_if_returns_index():
    tw = _tw("alpha", "beta", "gamma")
    assert taut.tab_index_if(tw, tw.widget(2)) == 2


def test_tab_index_if_not_found_returns_negative_one():
    tw = _tw("alpha")
    assert taut.tab_index_if(tw, QWidget()) == -1


def test_tab_index_if_empty_returns_negative_one():
    assert taut.tab_index_if(QTabWidget(), QWidget()) == -1


# ---------------------------------------------------------------------------
# tab_index_by_name
# ---------------------------------------------------------------------------


def test_tab_index_by_name_returns_correct_index():
    tw = _tw("alpha", "beta", "gamma")
    assert taut.tab_index_by_name(tw, "gamma") == 2


def test_tab_index_by_name_first_tab():
    tw = _tw("alpha", "beta")
    assert taut.tab_index_by_name(tw, "alpha") == 0


def test_tab_index_by_name_not_found_raises():
    tw = _tw("alpha")
    with pytest.raises(ValueError, match="missing"):
        taut.tab_index_by_name(tw, "missing")


def test_tab_index_by_name_empty_raises():
    with pytest.raises(ValueError):
        taut.tab_index_by_name(QTabWidget(), "anything")


# ---------------------------------------------------------------------------
# tab_index_by_name_if
# ---------------------------------------------------------------------------


def test_tab_index_by_name_if_returns_index():
    tw = _tw("alpha", "beta", "gamma")
    assert taut.tab_index_by_name_if(tw, "beta") == 1


def test_tab_index_by_name_if_not_found_returns_negative_one():
    tw = _tw("alpha")
    assert taut.tab_index_by_name_if(tw, "missing") == -1


def test_tab_index_by_name_if_empty_returns_negative_one():
    assert taut.tab_index_by_name_if(QTabWidget(), "anything") == -1


# ---------------------------------------------------------------------------
# tabs — list all widgets
# ---------------------------------------------------------------------------


def test_tabs_returns_all_widgets():
    tw = _tw("alpha", "beta", "gamma")
    assert len(taut.tabs(tw)) == 3


def test_tabs_preserves_order():
    tw = _tw("alpha", "beta", "gamma")
    names = [w.objectName() for w in taut.tabs(tw)]
    assert names == ["alpha", "beta", "gamma"]


def test_tabs_empty_returns_empty_list():
    assert taut.tabs(QTabWidget()) == []


def test_tabs_single_widget():
    tw = _tw("only")
    result = taut.tabs(tw)
    assert len(result) == 1
    assert result[0].objectName() == "only"


# ---------------------------------------------------------------------------
# has_type
# ---------------------------------------------------------------------------


def test_has_type_returns_true_when_type_present():
    tw = _tw("alpha")
    assert taut.has_type(tw, QWidget) is True


def test_has_type_returns_false_when_type_absent():
    """QTabWidget itself is not one of the child tabs."""
    tw = _tw("alpha")
    assert taut.has_type(tw, QTabWidget) is False


def test_has_type_empty_returns_false():
    assert taut.has_type(QTabWidget(), QWidget) is False


# ---------------------------------------------------------------------------
# select_tab — int path
# ---------------------------------------------------------------------------


def test_select_tab_by_int_sets_current_index():
    tw = _tw("alpha", "beta", "gamma")
    result = taut.select_tab(tw, 2)
    assert result is True
    assert tw.currentIndex() == 2


def test_select_tab_by_int_zero():
    tw = _tw("alpha", "beta")
    tw.setCurrentIndex(1)
    result = taut.select_tab(tw, 0)
    assert result is True
    assert tw.currentIndex() == 0


def test_select_tab_by_int_out_of_range_raises():
    tw = _tw("alpha")
    with pytest.raises(ValueError, match="No such tab: 99"):
        taut.select_tab(tw, 99)


# ---------------------------------------------------------------------------
# select_tab — widget path (delegates to select_tab_widget)
# ---------------------------------------------------------------------------


def test_select_tab_by_widget_sets_current_index():
    tw = _tw("alpha", "beta", "gamma")
    widget = tw.widget(2)
    result = taut.select_tab(tw, widget)
    assert result is True
    assert tw.currentIndex() == 2


def test_select_tab_by_widget_not_found_returns_false():
    tw = _tw("alpha")
    orphan = QWidget()
    orphan.setObjectName("orphan")
    assert taut.select_tab(tw, orphan) is False


# ---------------------------------------------------------------------------
# select_tab_widget
# ---------------------------------------------------------------------------


def test_select_tab_widget_sets_current_index():
    tw = _tw("alpha", "beta")
    widget = tw.widget(1)
    result = taut.select_tab_widget(tw, widget)
    assert result is True
    assert tw.currentIndex() == 1


def test_select_tab_widget_not_found_returns_false():
    tw = _tw("alpha")
    orphan = QWidget()
    orphan.setObjectName("orphan")
    assert taut.select_tab_widget(tw, orphan) is False


def test_select_tab_widget_empty_tab_widget_returns_false():
    orphan = QWidget()
    orphan.setObjectName("orphan")
    assert taut.select_tab_widget(QTabWidget(), orphan) is False
