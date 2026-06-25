"""
pytest-qt tests for cut, copy, and paste operations inside content viewers.

Checklist coverage:
  HOME > file content ops: cut, copy, paste inside editors
    - cut in text editors (csvpath, MD, JSON)
    - copy lines in grid
    - copy irregular cell selection in grid
    - paste in grid
    - paste-as-new in grid (creates deconflicted copy)

== Text editors ==

CsvpathViewer, MdViewer, and JsonViewer2 all embed QPlainTextEdit / QTextEdit
subclasses.  Qt's built-in cut()/copy()/paste() methods work directly and
update QApplication.clipboard().  The tests open files as EDITABLE (the
normal left-sidebar path), select text programmatically, and assert the
clipboard and editor state.

  - CsvpathViewer.text_edit  → CsvPathTextEdit  (QPlainTextEdit subclass)
  - MdViewer.text_edit       → MdTextEdit       (QTextEdit subclass)
  - JsonViewer2.view         → JsonEditor       (QPlainTextEdit subclass)

Note: setReadOnly(True) is applied to CsvpathViewer's text_edit when
UNEDITABLE, which blocks built-in cut/paste at the Qt widget level.
MdTextEdit and JsonEditor do NOT use setReadOnly; they block edits through
keyPressEvent instead.  All tests use EDITABLE viewers.

== Grid (DataViewer) ==

DataViewer.copy_selection_to_clipboard() serialises selected cells as
  [[row, col, value], ...]
in JSON and puts the result in QApplication.clipboard().

DataViewer.paste_from_clipboard() reads that JSON from the clipboard and
writes each cell to the model at (dest_row + delta_row, dest_col + delta_col),
anchored at the current selection index.

DataViewer._copy_to_new() prompts for a filename via QInputDialog then
writes selected cells to a new CSV via _write_new_from_selected().  The
dialog is monkeypatched; the resulting file path is computed using
_relative_path_to_parent_dir(), matching the production code path.

test.csv content (headers are row 0 in the TableModel):
  Row 0: ["firstname", "lastname", "say"]
  Row 1: ["cat",       "bert",     "miew"]
  Row 2: ["dog",       "brat",     "bark"]

Run with:
  QT_QPA_PLATFORM=offscreen poetry run python -m pytest tests/gui/test_content_copy_paste.py -v
"""

import json
import os

from PySide6.QtCore import QItemSelection, QItemSelectionModel, Qt
from PySide6.QtWidgets import QAbstractItemView, QApplication

from flightpath.util.tabs_utility import TabsUtility as taut
from flightpath.widgets.panels.csvpath_viewer import CsvpathViewer
from flightpath.widgets.panels.data_viewer import DataViewer
from flightpath.widgets.panels.json_viewer_2 import JsonViewer2
from flightpath.widgets.panels.md_viewer import MdViewer

# isolated_home and main fixtures are provided by conftest.py

TIMEOUT = 8000  # ms — file workers run on the Qt thread pool


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _examples(main, *parts) -> str:
    return os.path.join(main.state.cwd, "examples", *parts)


def _open_and_wait(qtbot, main, path: str):
    """Open a file (EDITABLE, the default) and block until its tab appears."""
    main.read_validate_and_display_file_for_path(path)
    qtbot.waitUntil(
        lambda: taut.find_tab(main.content.tab_widget, path) is not None,
        timeout=TIMEOUT,
    )
    return taut.find_tab(main.content.tab_widget, path)[1]


def _clipboard_cells(viewer: DataViewer) -> dict:
    """Parse clipboard JSON from copy_selection_to_clipboard; return {(r,c): value}."""
    raw = QApplication.clipboard().text()
    return {(r, c): v for r, c, v in json.loads(raw)}


# ---------------------------------------------------------------------------
# Tests — text editor copy
# ---------------------------------------------------------------------------


def test_csvpath_editor_copy_to_clipboard(qtbot, main):
    """
    Selecting all text in a CsvpathViewer and calling copy() must put the
    file's content in the clipboard without modifying the editor.

    CsvpathViewer.text_edit is a CsvPathTextEdit (QPlainTextEdit subclass);
    copy() is a direct Qt method and does not go through keyPressEvent.
    """
    path = _examples(main, "first steps", "Hello World.csvpath")
    viewer = _open_and_wait(qtbot, main, path)
    assert isinstance(viewer, CsvpathViewer)

    original = viewer.text_edit.toPlainText()
    assert len(original) > 0, "Csvpath file must have content before copy"

    viewer.text_edit.selectAll()
    viewer.text_edit.copy()

    assert QApplication.clipboard().text() == original, (
        "Clipboard must contain the selected csvpath text after copy()"
    )
    assert viewer.text_edit.toPlainText() == original, (
        "copy() must leave the editor content unchanged"
    )

#chked
def test_csvpath_editor_cut_clears_editor(qtbot, main):
    """
    Selecting all text in a CsvpathViewer and calling cut() must place the
    text in the clipboard and leave the editor empty.

    CsvpathViewer opens with EDITABLE (left-sidebar default), so
    setReadOnly(False) and cut() is permitted at the Qt level.
    """
    path = _examples(main, "first steps", "Hello World.csvpath")
    viewer = _open_and_wait(qtbot, main, path)
    assert isinstance(viewer, CsvpathViewer)

    original = viewer.text_edit.toPlainText()
    assert len(original) > 0, "Csvpath file must have content before cut"

    viewer.text_edit.selectAll()
    viewer.text_edit.cut()

    assert QApplication.clipboard().text() == original, (
        "Clipboard must contain the cut csvpath text"
    )
    assert viewer.text_edit.toPlainText() == "", (
        "Editor must be empty after cut() on a full selection"
    )


# ---------------------------------------------------------------------------
# Tests — MD editor copy
# ---------------------------------------------------------------------------


def test_md_editor_copy_to_clipboard(qtbot, main):
    """
    Selecting all text in a MdViewer and calling copy() must put content in
    the clipboard.

    MdViewer.text_edit is a MdTextEdit (QTextEdit subclass); for .md files
    the content is loaded via setMarkdown(), so the clipboard receives the
    rendered plain text (markdown syntax stripped) rather than the raw source.
    The test asserts non-empty clipboard content only.
    """
    path = _examples(main, "first steps", "README.md")
    viewer = _open_and_wait(qtbot, main, path)
    assert isinstance(viewer, MdViewer)
    assert viewer.text_edit is not None

    viewer.text_edit.selectAll()
    viewer.text_edit.copy()

    clipped = QApplication.clipboard().text()
    assert len(clipped) > 0, (
        "Clipboard must be non-empty after copying from an MdViewer"
    )


# ---------------------------------------------------------------------------
# Tests — JSON editor cut and paste
# ---------------------------------------------------------------------------


def test_json_editor_copy_to_clipboard(qtbot, main):
    """
    Selecting all text in a JsonViewer2 and calling copy() must put the JSON
    content in the clipboard.

    JsonViewer2.view is a JsonEditor (QPlainTextEdit subclass).  copy() is a
    direct method that bypasses keyPressEvent, so it works for EDITABLE.
    """
    path = _examples(main, "named-paths groups", "my_named_paths.json")
    viewer = _open_and_wait(qtbot, main, path)
    assert isinstance(viewer, JsonViewer2)

    original = viewer.view.toPlainText()
    assert len(original) > 0, "JSON file must have content before copy"

    viewer.view.selectAll()
    viewer.view.copy()

    assert len(QApplication.clipboard().text()) > 0, (
        "Clipboard must be non-empty after copying from a JsonViewer2"
    )
    assert viewer.view.toPlainText() == original, (
        "copy() must not modify the editor content"
    )

#chked
def test_json_editor_cut_clears_editor(qtbot, main):
    """
    Selecting all text in a JsonViewer2 and calling cut() must place the
    content in the clipboard and empty the editor.

    JsonEditor does not use setReadOnly(); UNEDITABLE protection goes through
    keyPressEvent only.  Direct cut() therefore works for EDITABLE viewers.
    """
    path = _examples(main, "named-paths groups", "my_named_paths.json")
    viewer = _open_and_wait(qtbot, main, path)
    assert isinstance(viewer, JsonViewer2)

    original = viewer.view.toPlainText()
    assert len(original) > 0, "JSON file must have content before cut"

    viewer.view.selectAll()
    viewer.view.cut()

    assert len(QApplication.clipboard().text()) > 0, (
        "Clipboard must have content after cut()"
    )
    assert viewer.view.toPlainText() == "", (
        "Editor must be empty after cut() on a full selection"
    )
    qtbot.wait(10000)


def test_json_editor_paste_inserts_text(qtbot, main):
    """
    Placing text in the clipboard and calling paste() on a JsonViewer2 must
    insert that text into the editor at the cursor position.

    The test clears the editor first (selectAll + cut), then sets clipboard
    text to known JSON and pastes.  The editor must contain the pasted text.
    """
    path = _examples(main, "named-paths groups", "my_named_paths.json")
    viewer = _open_and_wait(qtbot, main, path)
    assert isinstance(viewer, JsonViewer2)

    # Clear the editor
    viewer.view.selectAll()
    viewer.view.cut()
    assert viewer.view.toPlainText() == ""

    # Set clipboard and paste
    payload = '{"paste_test": true}'
    QApplication.clipboard().setText(payload)
    viewer.view.paste()

    assert payload in viewer.view.toPlainText(), (
        "Pasted JSON must appear in the editor after paste()"
    )


# ---------------------------------------------------------------------------
# Tests — grid copy (single cell, rectangular, irregular)
# ---------------------------------------------------------------------------

#chked
def test_grid_copy_single_cell(qtbot, main):
    """
    Selecting a single cell and calling copy_selection_to_clipboard() must
    place a JSON array with exactly one cell tuple in the clipboard.

    Cell (0, 0) in test.csv is 'firstname' (the header row is data row 0
    in the TableModel).
    """
    path = _examples(main, "first steps", "test.csv")
    viewer = _open_and_wait(qtbot, main, path)
    assert isinstance(viewer, DataViewer)

    model = viewer.table_view.model()
    sm = viewer.table_view.selectionModel()
    idx = model.index(0, 0)
    sm.setCurrentIndex(idx, QItemSelectionModel.ClearAndSelect)

    viewer.copy_selection_to_clipboard()

    cells = _clipboard_cells(viewer)
    assert (0, 0) in cells, "Clipboard must contain cell (0, 0)"
    assert cells[(0, 0)] == "firstname", (
        "Cell (0, 0) of test.csv must be 'firstname'"
    )
    assert len(cells) == 1, "Single-cell selection must copy exactly one cell"

#chked
def test_grid_copy_rectangular_selection(qtbot, main):
    """
    Selecting a 2×2 rectangle and calling copy_selection_to_clipboard() must
    place all four cells in the clipboard JSON.

    Selection (0,0)→(1,1) covers:
      (0,0)="firstname"  (0,1)="lastname"
      (1,0)="cat"        (1,1)="bert"
    """
    path = _examples(main, "first steps", "test.csv")
    viewer = _open_and_wait(qtbot, main, path)
    assert isinstance(viewer, DataViewer)

    model = viewer.table_view.model()
    sm = viewer.table_view.selectionModel()
    rect = QItemSelection(model.index(0, 0), model.index(1, 1))
    sm.select(rect, QItemSelectionModel.ClearAndSelect)

    viewer.copy_selection_to_clipboard()

    cells = _clipboard_cells(viewer)
    assert len(cells) == 4, f"2×2 selection must yield 4 cells; got {len(cells)}"
    assert cells.get((0, 0)) == "firstname"
    assert cells.get((0, 1)) == "lastname"
    assert cells.get((1, 0)) == "cat"
    assert cells.get((1, 1)) == "bert"

#chked
def test_grid_copy_irregular_selection(qtbot, main):
    """
    Selecting two non-adjacent cells and calling copy_selection_to_clipboard()
    must place both cells in the clipboard JSON.

    Cells (0, 0) and (2, 2) are not in the same row or column and are not
    adjacent.  QTableView must be in ExtendedSelection mode to allow this;
    the test sets that mode explicitly.

    copy_selection_to_clipboard() iterates selectedIndexes() directly,
    so it handles irregular (non-rectangular) selections naturally.
    """
    path = _examples(main, "first steps", "test.csv")
    viewer = _open_and_wait(qtbot, main, path)
    assert isinstance(viewer, DataViewer)

    viewer.table_view.setSelectionMode(QAbstractItemView.ExtendedSelection)
    model = viewer.table_view.model()
    sm = viewer.table_view.selectionModel()

    # Select (0,0) then add (2,2) without clearing
    sm.select(model.index(0, 0), QItemSelectionModel.ClearAndSelect)
    sm.select(model.index(2, 2), QItemSelectionModel.Select)

    viewer.copy_selection_to_clipboard()

    cells = _clipboard_cells(viewer)
    assert (0, 0) in cells, "Irregular selection must include cell (0, 0)"
    assert (2, 2) in cells, "Irregular selection must include cell (2, 2)"
    assert cells[(0, 0)] == "firstname", "Cell (0,0) must be 'firstname'"
    assert cells[(2, 2)] == "bark", "Cell (2,2) must be 'bark'"


# ---------------------------------------------------------------------------
# Tests — grid paste
# ---------------------------------------------------------------------------

#chked
def test_grid_paste_single_cell(qtbot, main):
    """
    Loading the clipboard with a single-cell JSON payload and calling
    paste_from_clipboard() must write the value into the model at the
    currently-selected cell.

    The paste is anchored at the current selection index (row 1, col 0 here).
    After paste, model.data((1, 0)) must equal the pasted value.

    Note: paste_from_clipboard() calls model.setData() which always succeeds
    regardless of the TableModel's editable flag — the EDITABLE guard is in
    the Ctrl+V keyPressEvent handler only.
    """
    path = _examples(main, "first steps", "test.csv")
    viewer = _open_and_wait(qtbot, main, path)
    assert isinstance(viewer, DataViewer)

    model = viewer.table_view.model()
    sm = viewer.table_view.selectionModel()

    # Source: cell at (0, 0), value "firstname", pasted to target (1, 0)
    payload = json.dumps([[0, 0, "pasted_value"]])
    QApplication.clipboard().setText(payload)

    target = model.index(1, 0)
    sm.setCurrentIndex(target, QItemSelectionModel.ClearAndSelect)

    viewer.paste_from_clipboard()

    result = model.data(target, Qt.DisplayRole)
    assert result == "pasted_value", (
        f"Cell (1, 0) must be 'pasted_value' after paste; got {result!r}"
    )

#chked
def test_grid_paste_multi_cell(qtbot, main):
    """
    A multi-cell clipboard payload must paste all cells relative to the
    anchor (the current selection index).

    Payload: two cells from (1,0) and (1,1) → pasted at anchor (2,0) they
    land at (2,0) and (2,1).
    """
    path = _examples(main, "first steps", "test.csv")
    viewer = _open_and_wait(qtbot, main, path)
    assert isinstance(viewer, DataViewer)

    model = viewer.table_view.model()
    sm = viewer.table_view.selectionModel()

    # Two cells: source (1,0) and (1,1) — will land at dest (2,0) and (2,1)
    payload = json.dumps([[1, 0, "alpha"], [1, 1, "beta"]])
    QApplication.clipboard().setText(payload)

    anchor = model.index(2, 0)
    sm.setCurrentIndex(anchor, QItemSelectionModel.ClearAndSelect)

    viewer.paste_from_clipboard()

    assert model.data(model.index(2, 0), Qt.DisplayRole) == "alpha", (
        "Cell (2, 0) must be 'alpha' after multi-cell paste"
    )
    assert model.data(model.index(2, 1), Qt.DisplayRole) == "beta", (
        "Cell (2, 1) must be 'beta' after multi-cell paste"
    )


# ---------------------------------------------------------------------------
# Tests — paste-as-new (copy selected cells to a new CSV file)
# ---------------------------------------------------------------------------

#chked
def test_grid_paste_as_new_creates_csv(monkeypatch, qtbot, main):
    """
    Selecting cells and calling _copy_to_new() must write them to a new CSV
    file whose path is determined by _relative_path_to_parent_dir().

    QInputDialog is monkeypatched to immediately return 'selection' without
    showing a dialog.  The resulting file is verified to exist and to have
    the expected row count (the selected 2×1 block → 2 data rows).
    """
    path = _examples(main, "first steps", "test.csv")
    viewer = _open_and_wait(qtbot, main, path)
    assert isinstance(viewer, DataViewer)

    # Select rows 1-2 in column 0: "cat" and "dog"
    model = viewer.table_view.model()
    sm = viewer.table_view.selectionModel()
    rect = QItemSelection(model.index(1, 0), model.index(2, 0))
    sm.select(rect, QItemSelectionModel.ClearAndSelect)

    class _FakeInputDialog:
        def setFixedSize(self, *a): pass
        def setLabelText(self, *a): pass
        def setTextValue(self, *a): pass
        def exec(self): return 1  # accepted
        def textValue(self): return "selection"

    monkeypatch.setattr(
        "flightpath.widgets.panels.data_viewer.QInputDialog", _FakeInputDialog
    )

    viewer._copy_to_new()

    # Reconstruct the output path using the same formula as _copy_to_new()
    rel_dir = viewer._relative_path_to_parent_dir()
    expected = os.path.join(main.state.cwd, rel_dir, "selection.csv")
    assert os.path.isfile(expected), (
        f"paste-as-new must create selection.csv at: {expected}"
    )
    with open(expected) as f:
        lines = [ln for ln in f.readlines() if ln.strip()]
    assert len(lines) == 2, (
        f"selection.csv must have 2 rows (one per selected row); got {len(lines)}"
    )
