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
# Tests — sampling row-count guarantees (HOME > data toolbar)
# ---------------------------------------------------------------------------


def test_random_all_gives_same_count_as_first_n(monkeypatch, qtbot, main):
    """
    RANDOM_ALL must produce the same row count as FIRST_N for the same row
    limit: both are capped at sample_size rows, they just pick different lines.
    RANDOM_0 is probabilistic — with randint forced to reject every line, it
    produces zero rows, which is correct but alarming if you don't expect it.

    This test exists to document the intended difference so that a low RANDOM_0
    count can be distinguished from a bug:
      FIRST_N 50   → takes first 50 lines
      RANDOM_ALL   → pre-selects 50 random line numbers; rowCount still 50
      RANDOM_0 (all-reject) → zero rows; the cap was never reached, not a bug
    """
    path = _large_csv_path(main)
    assert os.path.exists(path), f"Large example CSV missing: {path}"

    # Default open: FIRST_N + SMALL (50) row limit
    viewer = _open_csv(qtbot, main, path)
    first_n_count = viewer.table_view.model().rowCount()
    assert first_n_count == DataConst.SMALL, (
        "FIRST_N on a large file must return exactly SMALL rows"
    )

    # RANDOM_ALL — prep_sampling pre-selects exactly sample_size line numbers
    rall_index = main.content.toolbar.sampling.findText(DataConst.RANDOM_ALL)
    _trigger_sampling_reload(qtbot, main, viewer, sampling_index=rall_index)
    assert viewer.table_view.model().rowCount() == first_n_count, (
        "RANDOM_ALL must return the same row count as FIRST_N; "
        "it samples different lines but the same number"
    )

    # RANDOM_0 with all-reject: randint always returns 1 → condition False → 0 rows
    monkeypatch.setattr(_random, "randint", lambda a, b: 1)
    r0_index = main.content.toolbar.sampling.findText(DataConst.RANDOM_0)
    _trigger_sampling_reload(qtbot, main, viewer, sampling_index=r0_index)
    assert viewer.table_view.model().rowCount() == 0, (
        "RANDOM_0 with randint always rejecting must produce 0 rows; "
        "this is the expected extreme of probabilistic sampling, not data loss"
    )


def test_row_limit_caps_all_sampling_modes(monkeypatch, qtbot, main):
    """
    The SMALL (50) row limit must be respected by every sampling mode.

    With a large file and a 50-row cap:
      FIRST_N    — takes first 50 lines → rowCount == 50
      RANDOM_ALL — pre-selects exactly 50 random lines → rowCount == 50
      RANDOM_0   — with randint forced to 0 (always accept), fills to cap → 50

    If any mode silently ignored the cap, a user switching sampling on a large
    file could load far more rows than the UI shows.
    """
    path = _large_csv_path(main)
    assert os.path.exists(path), f"Large example CSV missing: {path}"

    viewer = _open_csv(qtbot, main, path)
    assert viewer.table_view.model().rowCount() == DataConst.SMALL, (
        "FIRST_N must cap at SMALL rows"
    )

    rall_index = main.content.toolbar.sampling.findText(DataConst.RANDOM_ALL)
    _trigger_sampling_reload(qtbot, main, viewer, sampling_index=rall_index)
    assert viewer.table_view.model().rowCount() == DataConst.SMALL, (
        "RANDOM_ALL must respect the SMALL row cap"
    )

    monkeypatch.setattr(_random, "randint", lambda a, b: 0)
    r0_index = main.content.toolbar.sampling.findText(DataConst.RANDOM_0)
    _trigger_sampling_reload(qtbot, main, viewer, sampling_index=r0_index)
    assert viewer.table_view.model().rowCount() == DataConst.SMALL, (
        "RANDOM_0 must stop at the SMALL row cap even when all lines are accepted"
    )


def test_save_sample_passes_model_rows_not_full_file(monkeypatch, qtbot, main):
    """
    Save sample must write exactly the rows in the current grid model — the
    sampled subset — not the rows from the original file.

    With RANDOM_0 (randint forced to 0, all-accept) and a SMALL (50) row cap,
    the model holds 50 rows out of a 999-row file.  The reactor's on_save_sample
    calls model.get_data() and passes it to main.save_sample().  That data must
    be the 50-row sample, not the 999-row original.

    This pins down the confusing but correct UX sequence:
      open 999-row file  → FIRST_N shows 50 rows
      switch RANDOM_0    → shows ~50 rows (different lines, same cap)
      Save sample        → writes those ~50 rows; re-opening shows ~50, not 999
      switch RANDOM_0    → shows ~25 rows — still correct, not a bug
    """
    path = _large_csv_path(main)
    assert os.path.exists(path), f"Large example CSV missing: {path}"

    monkeypatch.setattr(_random, "randint", lambda a, b: 0)
    viewer = _open_csv(qtbot, main, path)

    r0_index = main.content.toolbar.sampling.findText(DataConst.RANDOM_0)
    _trigger_sampling_reload(qtbot, main, viewer, sampling_index=r0_index)

    model_rows = viewer.table_view.model().rowCount()
    assert model_rows == DataConst.SMALL, (
        "Setup: RANDOM_0 all-accept must fill to the SMALL cap"
    )

    # Intercept save_sample to capture the data the reactor passes to it.
    # Returning None skips the post-save file reload.
    captured = {}

    def _mock_save(*, path, name, data):
        captured["row_count"] = len(data)
        return None

    monkeypatch.setattr(main, "save_sample", _mock_save)

    # setCurrentWidget normalises the tab-widget state before on_save_sample
    # reads currentIndex() (same phantom-tab workaround as test_toggle_raw_view_on_csv)
    main.content.tab_widget.setCurrentWidget(viewer)
    main.reactor.on_save_sample()

    assert captured.get("row_count") == model_rows, (
        f"save_sample must receive exactly {model_rows} rows from the model; "
        f"got {captured.get('row_count')!r}"
    )

    with open(path) as f:
        total_lines = sum(1 for line in f if line.strip())
    assert model_rows < total_lines, (
        "The sampled model must be a strict subset of the source file"
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
