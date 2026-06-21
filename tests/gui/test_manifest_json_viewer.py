"""
pytest-qt tests for manifest.json opening as a JsonViewer grid.

Checklist coverage:
  HOME > right-column manifest.json opens in JSON grid (JsonViewer)

When a manifest.json file is selected in the right-side sidebars (named-files,
named-paths), the reactor's on_rt_tree_click() calls
read_validate_and_display_file() with editable=UNEDITABLE.  The resulting
JsonDataWorker emits (filepath, data, editable) → update_json_views(), which
branches on two conditions:

  filepath.endswith("manifest.json")  AND  editable == UNEDITABLE

When both hold → JsonViewer (read-only tree-grid widget).
Otherwise       → JsonViewer2 (text editor).

Tests:
  • named-file manifest.json → JsonViewer
  • JsonViewer has a populated model (root row count > 0)
  • named-paths manifest.json → JsonViewer
  • regular .json (not named manifest.json) → JsonViewer2  [contrast]
  • manifest.json + editable=EDITABLE → JsonViewer2       [contrast]

Run with:
  QT_QPA_PLATFORM=offscreen poetry run python -m pytest tests/gui/test_manifest_json_viewer.py -v
"""

import os

from PySide6.QtCore import QModelIndex

from flightpath.util.editable import EditStates
from flightpath.util.tabs_utility import TabsUtility as taut
from flightpath.widgets.panels.json_viewer import JsonViewer
from flightpath.widgets.panels.json_viewer_2 import JsonViewer2

# isolated_home and main fixtures are provided by conftest.py

TIMEOUT = 8000  # ms — JsonDataWorker runs on the Qt thread pool


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _examples(main, *parts) -> str:
    return os.path.join(main.state.cwd, "examples", *parts)


def _inputs_files_root(main) -> str:
    return main.csvpath_config.get(section="inputs", name="files")


def _inputs_csvpaths_root(main) -> str:
    return main.csvpath_config.get(section="inputs", name="csvpaths")


def _register_named_file(main, name: str = "test_manifest") -> str:
    """Register test.csv as a named-file; return the absolute path to its manifest.json."""
    csv_file = _examples(main, "first steps", "test.csv")
    csvpaths = main.csvpaths
    csvpaths.config.set(section="inputs", name="allow_local_files", value=True)
    csvpaths.file_manager.add_named_file(name=name, path=csv_file, template=None)
    return os.path.join(_inputs_files_root(main), name, "manifest.json")


def _register_named_paths(main, name: str = "test_manifest") -> str:
    """Register Hello World.csvpath; return the absolute path to its manifest.json."""
    csvpath_file = _examples(main, "first steps", "Hello World.csvpath")
    csvpaths = main.csvpaths
    csvpaths.config.set(section="inputs", name="allow_local_files", value=True)
    csvpaths.paths_manager.add_named_paths_from_file(
        name=name, file_path=csvpath_file, template=None, append=False
    )
    return os.path.join(_inputs_csvpaths_root(main), name, "manifest.json")


def _open_and_wait(qtbot, main, path: str, editable=EditStates.UNEDITABLE):
    """Open a file with the given editable state and block until its tab appears."""
    main.read_validate_and_display_file_for_path(path, editable=editable)
    qtbot.waitUntil(
        lambda: taut.find_tab(main.content.tab_widget, path) is not None,
        timeout=TIMEOUT,
    )
    return taut.find_tab(main.content.tab_widget, path)[1]


# ---------------------------------------------------------------------------
# Tests — manifest.json → JsonViewer (grid)
# ---------------------------------------------------------------------------


def test_named_file_manifest_opens_in_json_viewer(qtbot, main):
    """
    Clicking a named-file manifest.json in the right-side sidebar must open it
    in a JsonViewer (tree-grid), not a JsonViewer2 (text editor).

    The reactor path: on_rt_tree_click() sets editable=UNEDITABLE for all
    non-.md files → read_validate_and_display_file() → JsonDataWorker →
    update_json_views() sees endswith("manifest.json") + UNEDITABLE → JsonViewer.
    """
    manifest_path = _register_named_file(main)
    assert os.path.isfile(manifest_path), (
        f"manifest.json must exist on disk after registration: {manifest_path}"
    )

    viewer = _open_and_wait(qtbot, main, manifest_path)

    assert isinstance(viewer, JsonViewer), (
        "Named-file manifest.json must open in a JsonViewer (grid), not JsonViewer2"
    )
    assert not isinstance(viewer, JsonViewer2), (
        "Named-file manifest.json must not open in a JsonViewer2 (text editor)"
    )


def test_named_file_manifest_json_viewer_has_rows(qtbot, main):
    """
    The JsonViewer created for a named-file manifest.json must have a
    populated model.  rootItem.childCount() (= rowCount at the root) must be
    > 0 — at minimum 'name' and 'path' keys written by add_named_file().
    """
    manifest_path = _register_named_file(main)
    viewer = _open_and_wait(qtbot, main, manifest_path)
    assert isinstance(viewer, JsonViewer)

    assert viewer.model.rowCount(QModelIndex()) > 0, (
        "JsonViewer model must have at least one row after loading a named-file manifest.json"
    )


def test_named_paths_manifest_opens_in_json_viewer(qtbot, main):
    """
    Clicking a named-paths manifest.json must also produce a JsonViewer.
    The same update_json_views() branch applies regardless of which right-side
    sidebar the file came from; the path suffix and editable state are the
    only conditions checked.
    """
    manifest_path = _register_named_paths(main)
    assert os.path.isfile(manifest_path), (
        f"manifest.json must exist on disk after named-paths registration: {manifest_path}"
    )

    viewer = _open_and_wait(qtbot, main, manifest_path)

    assert isinstance(viewer, JsonViewer), (
        "Named-paths manifest.json must open in a JsonViewer (grid), not JsonViewer2"
    )


# ---------------------------------------------------------------------------
# Tests — contrast cases: JsonViewer2 instead of JsonViewer
# ---------------------------------------------------------------------------


def test_regular_json_opens_in_json_viewer2(qtbot, main):
    """
    A regular .json file (path does not end with 'manifest.json') must open
    in a JsonViewer2 (text editor) even when opened with UNEDITABLE.

    Contrast with the manifest.json tests: update_json_views() requires both
    conditions; a non-manifest path fails the first one.
    """
    path = _examples(main, "named-paths groups", "my_named_paths.json")
    viewer = _open_and_wait(qtbot, main, path, editable=EditStates.UNEDITABLE)

    assert isinstance(viewer, JsonViewer2), (
        "A regular .json file must open in a JsonViewer2, not a JsonViewer grid"
    )
    assert not isinstance(viewer, JsonViewer), (
        "A regular .json file must not open in a JsonViewer (grid)"
    )


def test_manifest_json_editable_opens_in_json_viewer2(qtbot, main):
    """
    A manifest.json opened with editable=EDITABLE must go to JsonViewer2.
    Both conditions (endswith + UNEDITABLE) are required; EDITABLE fails
    the second condition so the text-editor path is taken.

    This is the path used when the user chooses 'Edit as JSON' on a
    manifest.json from the left sidebar.
    """
    manifest_path = _register_named_file(main, name="test_editable_manifest")
    viewer = _open_and_wait(qtbot, main, manifest_path, editable=EditStates.EDITABLE)

    assert isinstance(viewer, JsonViewer2), (
        "A manifest.json opened with EDITABLE must open in a JsonViewer2, not a JsonViewer grid"
    )
