"""
pytest-qt tests for opening files in the content viewer.

Checklist coverage: HOME > open file; HOME > editors (CsvPath, JSON, Grid/raw, Markdown)

Each test calls read_validate_and_display_file_for_path(), which is exactly what
on_tree_click() calls after resolving the sidebar model index to a path. That function
is the dispatch point for all file-type routing, so one test per file type covers the
four distinct worker/viewer paths.

The tab's objectName is always the absolute file path, so taut.find_tab() confirms
both that a tab opened and that it belongs to the right file.

Run with:
  QT_QPA_PLATFORM=offscreen poetry run python -m pytest tests/gui/test_open_file.py -v
"""

import os

from flightpath.util.tabs_utility import TabsUtility as taut
from flightpath.widgets.panels.csvpath_viewer import CsvpathViewer
from flightpath.widgets.panels.data_viewer import DataViewer
from flightpath.widgets.panels.json_viewer_2 import JsonViewer2
from flightpath.widgets.panels.md_viewer import MdViewer

# isolated_home and main fixtures are provided by conftest.py

TIMEOUT = 5000  # ms — file workers run on the Qt thread pool


def _examples(main, *parts) -> str:
    """Absolute path to a file under the current project's examples/ directory."""
    return os.path.join(main.state.cwd, "examples", *parts)


def _open_and_wait(qtbot, main, path):
    """
    Dispatch a file open and block until its tab appears in content.tab_widget.
    Returns the viewer widget so callers can assert its type.
    """
    main.read_validate_and_display_file_for_path(path)
    qtbot.waitUntil(
        lambda: taut.find_tab(main.content.tab_widget, path) is not None,
        timeout=TIMEOUT,
    )
    return taut.find_tab(main.content.tab_widget, path)[1]


# ========= TESTS ============


def test_open_csvpath_file_opens_csvpath_viewer(qtbot, main):
    """A .csvpath file must open a CsvpathViewer tab and switch to the Content view."""
    path = _examples(main, "first steps", "Hello World.csvpath")
    assert os.path.exists(path), f"Example file missing: {path}"

    viewer = _open_and_wait(qtbot, main, path)

    assert isinstance(viewer, CsvpathViewer)
    assert main.main_layout.currentIndex() == 1


def test_open_csv_file_opens_data_viewer(qtbot, main):
    """A .csv file must open a DataViewer tab and switch to the Content view."""
    path = _examples(main, "first steps", "test.csv")
    assert os.path.exists(path), f"Example file missing: {path}"

    viewer = _open_and_wait(qtbot, main, path)

    assert isinstance(viewer, DataViewer)
    assert main.main_layout.currentIndex() == 1


def test_open_json_file_opens_json_viewer(qtbot, main):
    """A .json file must open a JsonViewer2 tab and switch to the Content view."""
    path = _examples(main, "named-paths groups", "my_named_paths.json")
    assert os.path.exists(path), f"Example file missing: {path}"

    viewer = _open_and_wait(qtbot, main, path)

    assert isinstance(viewer, JsonViewer2)
    assert main.main_layout.currentIndex() == 1


def test_open_md_file_opens_md_viewer(qtbot, main):
    """A .md file must open an MdViewer tab and switch to the Content view."""
    path = _examples(main, "first steps", "README.md")
    assert os.path.exists(path), f"Example file missing: {path}"

    viewer = _open_and_wait(qtbot, main, path)

    assert isinstance(viewer, MdViewer)
    assert main.main_layout.currentIndex() == 1
