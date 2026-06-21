"""
pytest-qt tests for the UNEDITABLE visual tint and copy-back prompt.

Checklist coverage:
  HOME > uneditable files are tinted green
  HOME > right-column files prompt copy-back when edit attempted

== Tinting ==

When a viewer is constructed with editable=UNEDITABLE, StyleUtility applies a
light-green (dark-green in dark mode) background to the inner content widget:

  DataViewer   → table_view   (QTableView)
  JsonViewer   → view         (KeyableTreeView)
  JsonViewer2  → view         (JsonEditor / QPlainTextEdit)
  CsvpathViewer → text_edit   (CsvPathTextEdit)

The color is StyleUtility.get_not_editable_color() (#f8fff8 light / #332a33
dark).  Tests assert the color string appears in the inner widget's
styleSheet().  The EDITABLE contrast test confirms the color is absent.

== Copy-back prompt ==

When the user tries to edit an UNEDITABLE viewer (save attempt, right-click),
the viewer calls _copy_back_question() which fires meut.yesNo2().  Tests
patch MessageUtility.yesNo2 to capture invocations and drive the answer.

Trigger paths tested:
  DataViewer.on_save()              → _copy_back_question() → yesNo2
  JsonViewer._show_context_menu()   → _copy_back_question() → yesNo2
  JsonViewer2._show_context_menu()  → _copy_back_question() → yesNo2

== Copy-back YES branch ==

_copy_back_answer(QMessageBox.Yes) calls fiut.copy_results_back_to_cwd()
synchronously, writing the file under cwd.  The test calls _copy_back_answer
directly, then checks the copied file exists on disk.

Run with:
  QT_QPA_PLATFORM=offscreen poetry run python -m pytest tests/gui/test_uneditable_tint_and_copy_back.py -v
"""

import os

from PySide6.QtCore import QPoint
from PySide6.QtWidgets import QMessageBox

from flightpath.util.editable import EditStates
from flightpath.util.message_utility import MessageUtility
from flightpath.util.style_utils import StyleUtility as stut
from flightpath.util.tabs_utility import TabsUtility as taut
from flightpath.widgets.panels.csvpath_viewer import CsvpathViewer
from flightpath.widgets.panels.data_viewer import DataViewer
from flightpath.widgets.panels.json_viewer import JsonViewer
from flightpath.widgets.panels.json_viewer_2 import JsonViewer2

# isolated_home and main fixtures are provided by conftest.py

TIMEOUT = 8000  # ms — file workers run on the Qt thread pool


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _examples(main, *parts) -> str:
    return os.path.join(main.state.cwd, "examples", *parts)


def _inputs_files_root(main) -> str:
    return main.csvpath_config.get(section="inputs", name="files")


def _register_named_file(main, name: str = "test_tint") -> str:
    """Register test.csv as a named-file; return path to its manifest.json."""
    csv_file = _examples(main, "first steps", "test.csv")
    csvpaths = main.csvpaths
    csvpaths.config.set(section="inputs", name="allow_local_files", value=True)
    csvpaths.file_manager.add_named_file(name=name, path=csv_file, template=None)
    return os.path.join(_inputs_files_root(main), name, "manifest.json")


def _open_and_wait(qtbot, main, path: str, editable=EditStates.UNEDITABLE):
    """Open *path* with the given editable state; return the viewer widget."""
    main.read_validate_and_display_file_for_path(path, editable=editable)
    qtbot.waitUntil(
        lambda: taut.find_tab(main.content.tab_widget, path) is not None,
        timeout=TIMEOUT,
    )
    return taut.find_tab(main.content.tab_widget, path)[1]


def _patch_yes_no2(monkeypatch, answer: int) -> list:
    """
    Replace MessageUtility.yesNo2 with a synchronous stub.  Returns a list
    that accumulates each call's msg string for assertion.
    """
    calls = []

    def _fake(*, parent, msg, title="", callback, args=None):
        calls.append(msg)
        callback(answer, **(args or {}))

    monkeypatch.setattr(MessageUtility, "yesNo2", _fake)
    return calls


# ---------------------------------------------------------------------------
# Tests — UNEDITABLE tint (green background applied)
# ---------------------------------------------------------------------------


def test_data_viewer_uneditable_tinted(qtbot, main):
    """
    A CSV file opened with UNEDITABLE must tint the DataViewer's table_view
    with the not-editable background color.

    DataViewer.__init__ calls stut.set_editable_background(self.table_view)
    which sets the stylesheet when editable != EDITABLE.
    """
    path = _examples(main, "first steps", "test.csv")
    viewer = _open_and_wait(qtbot, main, path)
    assert isinstance(viewer, DataViewer)

    expected = stut.get_not_editable_color()
    assert expected in viewer.table_view.styleSheet(), (
        f"UNEDITABLE DataViewer table_view must have {expected!r} in its styleSheet"
    )


def test_json_viewer_uneditable_tinted(qtbot, main):
    """
    A manifest.json opened with UNEDITABLE must tint the JsonViewer's
    KeyableTreeView (viewer.view) with the not-editable background color.

    KeyableTreeView.__init__ calls stut.set_editable_background(self) which
    sets the stylesheet when editable != EDITABLE.
    """
    manifest_path = _register_named_file(main)
    viewer = _open_and_wait(qtbot, main, manifest_path)
    assert isinstance(viewer, JsonViewer)

    expected = stut.get_not_editable_color()
    assert expected in viewer.view.styleSheet(), (
        f"UNEDITABLE JsonViewer's KeyableTreeView must have {expected!r} in its styleSheet"
    )


def test_json_viewer2_uneditable_tinted(qtbot, main):
    """
    A regular .json file opened with UNEDITABLE must tint the JsonViewer2's
    JsonEditor (viewer.view) with the not-editable background color.

    JsonEditor.__init__ calls stut.set_editable_background(self), which sets
    the stylesheet when editable != EDITABLE.
    """
    path = _examples(main, "named-paths groups", "my_named_paths.json")
    viewer = _open_and_wait(qtbot, main, path, editable=EditStates.UNEDITABLE)
    assert isinstance(viewer, JsonViewer2)

    expected = stut.get_not_editable_color()
    assert expected in viewer.view.styleSheet(), (
        f"UNEDITABLE JsonViewer2's JsonEditor must have {expected!r} in its styleSheet"
    )


def test_csvpath_viewer_uneditable_tinted(qtbot, main):
    """
    A csvpath file opened with UNEDITABLE must tint the CsvpathViewer's
    CsvPathTextEdit (viewer.text_edit) with the not-editable background color.

    CsvpathViewer.__init__ calls stut.set_editable_background(self.text_edit)
    which sets the stylesheet when editable != EDITABLE.
    """
    path = _examples(main, "first steps", "Hello World.csvpath")
    viewer = _open_and_wait(qtbot, main, path, editable=EditStates.UNEDITABLE)
    assert isinstance(viewer, CsvpathViewer)

    expected = stut.get_not_editable_color()
    assert expected in viewer.text_edit.styleSheet(), (
        f"UNEDITABLE CsvpathViewer's text_edit must have {expected!r} in its styleSheet"
    )


def test_data_viewer_editable_not_tinted(qtbot, main):
    """
    A CSV file opened with EDITABLE must NOT have the green tint on its
    table_view.  stut._set_editable_background() only applies the stylesheet
    when editable != EDITABLE, so the default (empty) stylesheet must remain.
    """
    path = _examples(main, "first steps", "test.csv")
    viewer = _open_and_wait(qtbot, main, path, editable=EditStates.EDITABLE)
    assert isinstance(viewer, DataViewer)

    expected = stut.get_not_editable_color()
    assert expected not in viewer.table_view.styleSheet(), (
        "EDITABLE DataViewer's table_view must NOT have the green tint"
    )


# ---------------------------------------------------------------------------
# Tests — copy-back prompt triggered when edit attempted
# ---------------------------------------------------------------------------


def test_data_viewer_on_save_prompts_copy_back(monkeypatch, qtbot, main):
    """
    Calling on_save() on an UNEDITABLE DataViewer must invoke yesNo2 to
    ask the user whether to copy the file back to the project.

    DataViewer.on_save() guards with:
      if self.editable == EditStates.UNEDITABLE: self._copy_back_question(); return
    """
    path = _examples(main, "first steps", "test.csv")
    viewer = _open_and_wait(qtbot, main, path)
    assert isinstance(viewer, DataViewer)

    calls = _patch_yes_no2(monkeypatch, QMessageBox.No)

    viewer.on_save()

    assert len(calls) == 1, (
        "on_save() on an UNEDITABLE DataViewer must invoke yesNo2 exactly once"
    )
    assert "copy" in calls[0].lower() or "edit" in calls[0].lower(), (
        f"yesNo2 message must mention copying or editing; got: {calls[0]!r}"
    )


def test_json_viewer_context_menu_prompts_copy_back(monkeypatch, qtbot, main):
    """
    Right-clicking an UNEDITABLE JsonViewer must invoke yesNo2.

    JsonViewer._show_context_menu() branches on editable immediately:
      if self.editable == EditStates.UNEDITABLE: self._copy_back_question(); return
    The position argument is unused in this path, so None is safe.
    """
    manifest_path = _register_named_file(main)
    viewer = _open_and_wait(qtbot, main, manifest_path)
    assert isinstance(viewer, JsonViewer)

    calls = _patch_yes_no2(monkeypatch, QMessageBox.No)

    viewer._show_context_menu(QPoint(0, 0))

    assert len(calls) == 1, (
        "Right-clicking an UNEDITABLE JsonViewer must invoke yesNo2 exactly once"
    )


def test_json_viewer2_context_menu_prompts_copy_back(monkeypatch, qtbot, main):
    """
    Right-clicking an UNEDITABLE JsonViewer2 must invoke yesNo2.

    JsonViewer2._show_context_menu() follows the same pattern as JsonViewer:
      if self.editable == EditStates.UNEDITABLE: self._copy_back_question(); return
    """
    path = _examples(main, "named-paths groups", "my_named_paths.json")
    viewer = _open_and_wait(qtbot, main, path, editable=EditStates.UNEDITABLE)
    assert isinstance(viewer, JsonViewer2)

    calls = _patch_yes_no2(monkeypatch, QMessageBox.No)

    viewer._show_context_menu(QPoint(0, 0))

    assert len(calls) == 1, (
        "Right-clicking an UNEDITABLE JsonViewer2 must invoke yesNo2 exactly once"
    )


# ---------------------------------------------------------------------------
# Tests — copy-back YES branch copies the file to the project
# ---------------------------------------------------------------------------


def test_copy_back_yes_copies_manifest_to_project(qtbot, main):
    """
    Answering Yes to the copy-back prompt on an UNEDITABLE JsonViewer must
    copy the file synchronously into the project's working directory.

    _copy_back_answer() calls fiut.copy_results_back_to_cwd() synchronously;
    the file lands under main.state.cwd before the method returns.  The test
    calls _copy_back_answer() directly to skip the async yesNo2 dialog.
    """
    manifest_path = _register_named_file(main)
    viewer = _open_and_wait(qtbot, main, manifest_path)
    assert isinstance(viewer, JsonViewer)

    viewer._copy_back_answer(QMessageBox.Yes)

    copied = os.path.join(main.state.cwd, "manifest.json")
    assert os.path.isfile(copied), (
        f"Answering Yes to copy-back must create a copy in cwd: {copied}"
    )
    with open(copied) as f:
        content = f.read()
    assert len(content) > 0, "Copied manifest.json must not be empty"


def test_copy_back_yes_copies_csv_to_project(monkeypatch, qtbot, main):
    """
    Answering Yes to the copy-back prompt on an UNEDITABLE DataViewer must
    copy the source CSV into the project's working directory.

    DataViewer._copy_back_answer() follows the same path as JsonViewer:
    calls fiut.copy_results_back_to_cwd() synchronously.

    The test patches read_validate_and_display_file_for_path to a no-op so the
    worker thread started by the copy-back (reopening the copied file) doesn't
    interfere with file-system assertions.
    """
    path = _examples(main, "first steps", "test.csv")
    viewer = _open_and_wait(qtbot, main, path)
    assert isinstance(viewer, DataViewer)

    # Suppress the subsequent file-open to keep the test focused
    monkeypatch.setattr(
        main, "read_validate_and_display_file_for_path", lambda *a, **kw: None
    )

    viewer._copy_back_answer(QMessageBox.Yes)

    copied = os.path.join(main.state.cwd, "test.csv")
    assert os.path.isfile(copied), (
        f"Answering Yes to copy-back on a DataViewer must create a copy in cwd: {copied}"
    )
