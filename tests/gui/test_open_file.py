"""
pytest-qt tests for opening files in the content viewer.

Checklist coverage:
  HOME > open file
  HOME > editors (CsvPath, JSON, Grid/raw, Markdown)
  HOME > open jsonl as json

Each test calls read_validate_and_display_file_for_path() (or
_do_edit_as_json() for the JSONL case), which is exactly what the sidebar
tree-click and context-menu handlers call.  That function is the dispatch
point for all file-type routing, so one test per file type covers the four
distinct worker/viewer paths.

The tab's objectName is always the absolute file path, so taut.find_tab()
confirms both that a tab opened and that it belongs to the right file.

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

#chked
def test_open_csvpath_file_opens_csvpath_viewer(qtbot, main):
    """A .csvpath file must open a CsvpathViewer tab and switch to the Content view."""
    path = _examples(main, "first steps", "Hello World.csvpath")
    assert os.path.exists(path), f"Example file missing: {path}"

    viewer = _open_and_wait(qtbot, main, path)

    assert isinstance(viewer, CsvpathViewer)
    assert main.main_layout.currentIndex() == 1

#chked
def test_open_csv_file_opens_data_viewer(qtbot, main):
    """A .csv file must open a DataViewer tab and switch to the Content view."""
    path = _examples(main, "first steps", "test.csv")
    assert os.path.exists(path), f"Example file missing: {path}"

    viewer = _open_and_wait(qtbot, main, path)

    assert isinstance(viewer, DataViewer)
    assert main.main_layout.currentIndex() == 1


#chked
def test_open_json_file_opens_json_viewer(qtbot, main):
    """A .json file must open a JsonViewer2 tab and switch to the Content view."""
    path = _examples(main, "named-paths groups", "my_named_paths.json")
    assert os.path.exists(path), f"Example file missing: {path}"

    viewer = _open_and_wait(qtbot, main, path)

    assert isinstance(viewer, JsonViewer2)
    assert main.main_layout.currentIndex() == 1

#chked
def test_open_md_file_opens_md_viewer(qtbot, main):
    """A .md file must open an MdViewer tab and switch to the Content view."""
    path = _examples(main, "first steps", "README.md")
    assert os.path.exists(path), f"Example file missing: {path}"

    viewer = _open_and_wait(qtbot, main, path)

    assert isinstance(viewer, MdViewer)
    assert main.main_layout.currentIndex() == 1

#chked
def test_open_jsonl_as_json(qtbot, main):
    """
    'Edit as JSON' on a .jsonl file must open a JsonViewer2 tab (editable)
    and switch to the Content view.  This exercises the sidebar context-menu
    path that calls _do_edit_as_json() → spin_up_json_worker().
    """
    path = _examples(main, "json", "prompts.jsonl")
    assert os.path.exists(path), f"Example JSONL missing: {path}"

    main.sidebar.actions._do_edit_as_json(path)
    qtbot.waitUntil(
        lambda: taut.find_tab(main.content.tab_widget, path) is not None,
        timeout=TIMEOUT,
    )

    viewer = taut.find_tab(main.content.tab_widget, path)[1]
    assert isinstance(viewer, JsonViewer2)
    assert main.main_layout.currentIndex() == 1
    qtbot.wait(2000)


