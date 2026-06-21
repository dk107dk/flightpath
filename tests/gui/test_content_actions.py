"""
pytest-qt tests for content-viewer toolbar actions.

Checklist coverage:
  HOME > open file > toggle raw/grid view
  HOME > open file > file info tab
  HOME > open file > change sampling rows

All three tests open the same example CSV file, perform a toolbar action,
and assert the expected UI state change without touching the main codebase.

The raw-source toggle and file-info actions are synchronous.
The rows-changed action triggers an async worker; the test waits for the
DataViewer's table model to be replaced to confirm the reload completed.

Run with:
  QT_QPA_PLATFORM=offscreen poetry run python -m pytest tests/gui/test_content_actions.py -v
"""

import os

from flightpath.util.tabs_utility import TabsUtility as taut
from flightpath.widgets.panels.data_viewer import DataViewer

# isolated_home and main fixtures are provided by conftest.py

TIMEOUT = 5000  # ms — file workers run on the Qt thread pool


def _csv_path(main) -> str:
    return os.path.join(main.state.cwd, "examples", "first steps", "test.csv")


def _open_csv(qtbot, main) -> DataViewer:
    """Open the example CSV and block until its DataViewer tab appears."""
    path = _csv_path(main)
    assert os.path.exists(path), f"Example CSV missing: {path}"
    main.selected_file_path = path
    main.read_validate_and_display_file_for_path(path)
    qtbot.waitUntil(
        lambda: taut.find_tab(main.content.tab_widget, path) is not None,
        timeout=TIMEOUT,
    )
    return taut.find_tab(main.content.tab_widget, path)[1]


# ========= TESTS ============


def test_toggle_raw_view_on_csv(qtbot, main):
    """
    Clicking 'Toggle source' on an open CSV must switch the DataViewer from
    grid view (layout index 0) to raw text view (layout index 1).
    """
    viewer = _open_csv(qtbot, main)
    assert isinstance(viewer, DataViewer)
    assert viewer.current_view_index == 0, "DataViewer should start in grid view"

    main.content.toolbar.raw_source.click()

    assert viewer.current_view_index == 1, "DataViewer should switch to raw view after toggle"


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
