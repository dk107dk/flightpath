"""
pytest-qt tests for content-viewer toolbar actions.

Checklist coverage:
  HOME > open file > toggle raw/grid view
  HOME > open file > file info tab
  HOME > open file > change sampling rows
  HOME > data toolbar > random sample — random sampling mode produces different rows
  HOME > data toolbar > set delimiter to view — toolbar delimiter changes how grid parses file

All tests open example CSV files, perform toolbar actions, and assert the
expected UI state change without touching the main codebase.

The raw-source toggle and file-info actions are synchronous.
The rows-changed, sampling, and delimiter actions trigger async workers; tests
wait for the DataViewer's table model to be replaced to confirm reload.

Run with:
  QT_QPA_PLATFORM=offscreen poetry run python -m pytest tests/gui/test_content_actions.py -v
"""

import os
import random as _random

from PySide6.QtCore import Qt

from flightpath.util.data_const import DataConst
from flightpath.util.tabs_utility import TabsUtility as taut
from flightpath.widgets.panels.data_viewer import DataViewer

# isolated_home and main fixtures are provided by conftest.py

TIMEOUT = 5000  # ms — file workers run on the Qt thread pool


def _csv_path(main) -> str:
    return os.path.join(main.state.cwd, "examples", "first steps", "test.csv")


def _large_csv_path(main) -> str:
    return os.path.join(main.state.cwd, "examples", "debugging", "World_Port_Index_sample.csv")


def _open_csv(qtbot, main, path: str = None) -> DataViewer:
    """Open a CSV and block until its DataViewer tab appears."""
    if path is None:
        path = _csv_path(main)
    assert os.path.exists(path), f"Example CSV missing: {path}"
    main.selected_file_path = path
    main.read_validate_and_display_file_for_path(path)
    qtbot.waitUntil(
        lambda: taut.find_tab(main.content.tab_widget, path) is not None,
        timeout=TIMEOUT,
    )
    return taut.find_tab(main.content.tab_widget, path)[1]


def _trigger_sampling_reload(qtbot, main, viewer: DataViewer, *, sampling_index: int) -> None:
    """Switch the sampling combo and wait for the table model to be replaced."""
    original_model = viewer.table_view.model()
    combo = main.content.toolbar.sampling
    combo.setCurrentIndex(sampling_index)
    combo.activated.emit(sampling_index)
    qtbot.waitUntil(
        lambda: viewer.table_view.model() is not original_model,
        timeout=TIMEOUT,
    )


# ========= TESTS ============

#chked
def test_toggle_raw_view_on_csv(qtbot, main):
    """
    Clicking 'Toggle source' on an open CSV must switch the DataViewer from
    grid view (layout index 0) to raw text view (layout index 1), and the
    raw text area must contain the file content.

    TODO: the below is worked around in regular use, but should be fixed so it's
    not broken behind the scenes:

    update_data_views() calls addTab() twice for a new file (once in the
    data_view-is-None branch at main.py:866, then unconditionally in the try
    block at main.py:900).  The second call moves the same widget inside the
    QTabWidget's stacked layout, leaving the tab bar and stacked widget out of
    sync: currentIndex() points at a phantom entry where widget(i) returns None.
    enable() then crashes on None.objectName() before select_tab is reached, so
    the phantom index persists.  on_raw_source() later receives None from
    widget(currentIndex()), raises AttributeError (silently caught by PySide6),
    and never calls toggle_grid_raw().

    Calling setCurrentWidget(viewer) before the click normalises the tab-widget
    state so that currentIndex() and widget(currentIndex()) are consistent.
    """
    viewer = _open_csv(qtbot, main)
    assert isinstance(viewer, DataViewer)
    assert viewer.current_view_index == 0, "DataViewer should start in grid view"

    # Re-select the viewer to recover from the phantom-tab state caused by the
    # double-addTab sequence in update_data_views (see docstring above).
    main.content.tab_widget.setCurrentWidget(viewer)

    main.content.toolbar.raw_source.click()

    assert viewer.current_view_index == 1, "DataViewer should switch to raw view after toggle"
    assert viewer.raw_view.text_edit.toPlainText() != "", (
        "Raw view must contain the file content after toggle"
    )

#chked
def test_file_info_opens_info_tab(qtbot, main):
    """
    Clicking 'File info' on an open CSV must add a 'File Info' tab to the
    helper panel's help_and_feedback tab widget.
    """
    _open_csv(qtbot, main)

    main.content.toolbar.file_info.click()

    info_tab = taut.find_tab(main.helper.help_and_feedback, "FileInfo")
    assert info_tab is not None, "Expected a 'File Info' tab in the helper panel"

def test_data_sampling_reloads_file(qtbot, main):
    """
    Changing the rows combo triggers a file reload.  The DataViewer tab must
    survive the reload and the table model must be replaced (confirming the
    worker ran to completion).
    """
    path = _csv_path(main)
    viewer = _open_csv(qtbot, main)
    assert isinstance(viewer, DataViewer)

    original_model = viewer.table_view.model()

    combo = main.content.toolbar.rows
    new_index = 1  # "250" rows
    combo.setCurrentIndex(new_index)
    combo.activated.emit(new_index)

    qtbot.waitUntil(
        lambda: viewer.table_view.model() is not original_model,
        timeout=TIMEOUT,
    )

    reloaded_viewer = taut.find_tab(main.content.tab_widget, path)[1]
    assert isinstance(reloaded_viewer, DataViewer)
    assert combo.currentIndex() == new_index


# ---------------------------------------------------------------------------
# Tests — random sampling mode (HOME > data toolbar > random sample)
# ---------------------------------------------------------------------------


def test_random_sample_zero_triggers_reload(qtbot, main):
    """
    Switching the sampling combo to 'Random from 0' must trigger a file reload
    that produces a valid, non-empty model with the correct column structure, and
    must leave the toolbar combo on RANDOM_0.

    GeneralDataWorker uses random.randint(0, 1) % 2 == 0 to decide whether
    to include each data line; the header row is always included.  columnCount()
    must match test.csv's 3-column structure regardless of which rows are sampled,
    and rowCount() must be at least 1 (the header).  The deterministic
    different-rows assertion lives in test_random_sampling_produces_different_rows.
    """
    viewer = _open_csv(qtbot, main)
    assert isinstance(viewer, DataViewer)

    r0_index = main.content.toolbar.sampling.findText(DataConst.RANDOM_0)
    _trigger_sampling_reload(qtbot, main, viewer, sampling_index=r0_index)

    reloaded = taut.find_tab(main.content.tab_widget, _csv_path(main))[1]
    assert isinstance(reloaded, DataViewer), (
        "DataViewer tab must survive a sampling mode change to RANDOM_0"
    )
    model = reloaded.table_view.model()
    assert model.columnCount() == 3, (
        "Column count must match test.csv's 3-column structure after RANDOM_0 reload"
    )
    assert model.rowCount() > 0, (
        "Model must contain at least the header row after RANDOM_0 reload"
    )
    assert main.content.toolbar.sampling.currentIndex() == r0_index, (
        "Sampling combo must remain on RANDOM_0 after reload"
    )


def test_random_sample_all_triggers_reload(qtbot, main):
    """
    Switching the sampling combo to 'Random from all' must trigger a file reload
    that produces a valid, non-empty model with the correct column structure, and
    must leave the toolbar combo on RANDOM_ALL.

    RANDOM_ALL pre-computes a random set of line numbers via prep_sampling()
    before reading the file (a two-pass approach).  columnCount() must match
    test.csv's 3-column structure and rowCount() must be at least 1 (the header).
    """
    viewer = _open_csv(qtbot, main)
    assert isinstance(viewer, DataViewer)

    rall_index = main.content.toolbar.sampling.findText(DataConst.RANDOM_ALL)
    _trigger_sampling_reload(qtbot, main, viewer, sampling_index=rall_index)

    reloaded = taut.find_tab(main.content.tab_widget, _csv_path(main))[1]
    assert isinstance(reloaded, DataViewer), (
        "DataViewer tab must survive a sampling mode change to RANDOM_ALL"
    )
    model = reloaded.table_view.model()
    assert model.columnCount() == 3, (
        "Column count must match test.csv's 3-column structure after RANDOM_ALL reload"
    )
    assert model.rowCount() > 0, (
        "Model must contain at least the header row after RANDOM_ALL reload"
    )
    assert main.content.toolbar.sampling.currentIndex() == rall_index, (
        "Sampling combo must remain on RANDOM_ALL after reload"
    )


def test_random_sampling_produces_different_rows(monkeypatch, qtbot, main):
    """
    'Random from 0' mode must vary which rows are included across reloads.

    GeneralDataWorker.accept_line() uses random.randint(0, 1) % 2 == 0 to
    decide whether to include a line.  This test drives that decision
    deterministically via monkeypatch:

      • First load — randint always returns 0  → condition is True → all rows taken
      • Second load — randint always returns 1 → condition is False → no rows taken

    The World Port Index sample (999 rows, capped at 50) provides enough rows
    to verify the contrasting behavior clearly.  If the sampling setting were
    being ignored and FIRST_N used instead, both loads would return the same
    non-zero count and the assertion would fail.
    """
    path = _large_csv_path(main)
    assert os.path.exists(path), f"Large example CSV missing: {path}"

    # --- First load: randint always returns 0 → every row is accepted ---
    monkeypatch.setattr(_random, "randint", lambda a, b: 0)
    viewer = _open_csv(qtbot, main, path)
    assert isinstance(viewer, DataViewer)

    main.content.toolbar.sampling.setCurrentIndex(
        main.content.toolbar.sampling.findText(DataConst.RANDOM_0)
    )
    _trigger_sampling_reload(
        qtbot, main, viewer,
        sampling_index=main.content.toolbar.sampling.currentIndex(),
    )
    rows_when_always_taken = viewer.table_view.model().rowCount()

    # --- Second load: randint always returns 1 → no rows accepted ---
    monkeypatch.setattr(_random, "randint", lambda a, b: 1)
    _trigger_sampling_reload(
        qtbot, main, viewer,
        sampling_index=main.content.toolbar.sampling.currentIndex(),
    )
    rows_when_never_taken = viewer.table_view.model().rowCount()

    assert rows_when_always_taken != rows_when_never_taken, (
        f"RANDOM_0 with randint→0 gave {rows_when_always_taken} rows, "
        f"with randint→1 gave {rows_when_never_taken} rows; they must differ"
    )
    assert rows_when_always_taken > 0, (
        "When randint always returns 0, at least some rows must be accepted"
    )


# ---------------------------------------------------------------------------
# Tests — delimiter to view (HOME > data toolbar > set delimiter to view)
# ---------------------------------------------------------------------------


def test_delimiter_change_affects_column_count(qtbot, main):
    """
    Changing the toolbar delimiter and triggering a reload must re-parse the
    file with the new delimiter, producing a different column count.

    test.csv is comma-delimited with 3 fields per row.  When re-parsed with
    the Pipe delimiter, each row has no pipe characters, so the whole row is
    treated as a single field — column count drops to 1.  Switching back to
    Comma restores the original 3-column layout.

    Regression guard: if delimiter_char() or the worker constructor stop
    reading the toolbar setting, the column count will stay at 3 for Pipe.
    """
    path = _csv_path(main)
    viewer = _open_csv(qtbot, main)
    assert isinstance(viewer, DataViewer)

    assert viewer.table_view.model().columnCount() == 3, (
        "test.csv with Comma delimiter must have 3 columns"
    )

    # --- Switch to Pipe delimiter → single column ---
    original_model = viewer.table_view.model()
    pipe_index = main.content.toolbar.delimiter.findText(DataConst.PIPE)
    main.content.toolbar.delimiter.setCurrentIndex(pipe_index)
    main.content.toolbar.delimiter.activated.emit(pipe_index)
    qtbot.waitUntil(
        lambda: viewer.table_view.model() is not original_model,
        timeout=TIMEOUT,
    )

    assert viewer.table_view.model().columnCount() == 1, (
        "test.csv re-parsed with Pipe delimiter must collapse to 1 column "
        "(no pipes in the file content)"
    )

    # --- Switch back to Comma → 3 columns restored ---
    original_model = viewer.table_view.model()
    comma_index = main.content.toolbar.delimiter.findText(DataConst.COMMA)
    main.content.toolbar.delimiter.setCurrentIndex(comma_index)
    main.content.toolbar.delimiter.activated.emit(comma_index)
    qtbot.waitUntil(
        lambda: viewer.table_view.model() is not original_model,
        timeout=TIMEOUT,
    )

    assert viewer.table_view.model().columnCount() == 3, (
        "test.csv re-parsed with Comma delimiter must restore 3 columns"
    )
