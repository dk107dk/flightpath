"""
pytest-qt tests for save and save-as across all content viewer types.

Checklist coverage:
  HOME > save, save-as > csvpath
  HOME > save, save-as > json
  HOME > save, save-as > json save-as triggers input2 dialog
  HOME > save, save-as > jsonl (in JsonViewer2)
  HOME > save, save-as > grid (CSV)
  HOME > delimiters > save data as new delimiter
  HOME > delimiters > save data with single-quote quotechar
  HOME > save, save-as > jsonl (in grid — forces save-as to CSV)

Save paths:

  CsvpathViewer: Ctrl-S → CsvPathTextEdit.on_save() → DataFileWriter
    - saves in place; file modified synchronously

  DataViewer (CSV): Ctrl-S → DataViewer.on_save() → _save() → _save_csv_grid()
    - saves in place with current delimiter/quotechar; synchronous

  DataViewer save-as: SaveCsvToDialog → _save_one_of(path, delimiter, quotechar, exts)
    - delimiter options: Comma→"," Pipe→"|" Semi-colon→";" Tab→"\\t"
    - saved via DELIMITERS dict (lowercased key lookup)

  DataViewer (JSONL/XLSX): on_save() detects extension → redirects to on_save_as()
    - shows SaveCsvToDialog; the dialog is monkeypatched in the redirect tests

  JsonViewer2: Ctrl-S → _save() → _do_save(self.path)
    - suffix in [jsonl, ndjson, jsonlines] → format as JSONL lines
    - otherwise → pretty-print as JSON
    - synchronous; save-as done via _save_as_continue((path, ok))

Run with:
  QT_QPA_PLATFORM=offscreen poetry run python -m pytest tests/gui/test_save_as.py -v
"""

import os

from flightpath.util.data_const import DataConst
from flightpath.util.message_utility import MessageUtility
from flightpath.util.tabs_utility import TabsUtility as taut
from flightpath.widgets.panels.csvpath_viewer import CsvpathViewer
from flightpath.widgets.panels.data_viewer import DataViewer
from flightpath.widgets.panels.json_viewer_2 import JsonViewer2

# isolated_home and main fixtures are provided by conftest.py

TIMEOUT = 8000  # ms — file workers run on the Qt thread pool


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _examples(main, *parts) -> str:
    return os.path.join(main.state.cwd, "examples", *parts)


def _open_and_wait(qtbot, main, path: str):
    """Dispatch a file open and block until its tab appears. Returns the viewer widget."""
    main.read_validate_and_display_file_for_path(path)
    qtbot.waitUntil(
        lambda: taut.find_tab(main.content.tab_widget, path) is not None,
        timeout=TIMEOUT,
    )
    return taut.find_tab(main.content.tab_widget, path)[1]


def _open_as_json_and_wait(qtbot, main, path: str):
    """Open a file via 'Edit as JSON' and block until its JsonViewer2 tab appears."""
    main.sidebar.actions._do_edit_as_json(path)
    qtbot.waitUntil(
        lambda: taut.find_tab(main.content.tab_widget, path) is not None,
        timeout=TIMEOUT,
    )
    return taut.find_tab(main.content.tab_widget, path)[1]


# ---------------------------------------------------------------------------
# Tests — csvpath
# ---------------------------------------------------------------------------

#chked
def test_csvpath_save_writes_changes(qtbot, main):
    """
    Editing a csvpath file and pressing save (CsvPathTextEdit.on_save) must
    write the changed text to disk synchronously.
    """
    path = _examples(main, "first steps", "Hello World.csvpath")
    viewer = _open_and_wait(qtbot, main, path)
    assert isinstance(viewer, CsvpathViewer)

    viewer.text_edit.appendPlainText("~ test-save-marker~")
    viewer.text_edit.on_save()

    with open(path) as f:
        contents = f.read()
    assert "test-save-marker" in contents, (
        "Saved csvpath file must contain the appended text"
    )


# ---------------------------------------------------------------------------
# Tests — CSV grid save-as with delimiter
# ---------------------------------------------------------------------------

#chked
def test_csv_save_as_comma_delimiter(qtbot, main):
    """
    Saving a CSV file via _save_one_of with Comma delimiter must write a
    comma-separated file; the header row must contain commas.
    """
    path = _examples(main, "first steps", "test.csv")
    viewer = _open_and_wait(qtbot, main, path)
    assert isinstance(viewer, DataViewer)

    output = os.path.join(main.state.cwd, "out_comma.csv")
    viewer._save_one_of(
        path=output,
        delimiter="Comma",
        quotechar="Double quotes",
        exts=["csv"],
    )

    assert os.path.isfile(output), f"Expected output CSV at: {output}"
    with open(output) as f:
        first_line = f.readline()
    assert "," in first_line, "Comma-delimited output must contain commas in header"

#chked
def test_csv_save_as_pipe_delimiter(qtbot, main):
    """
    Saving a CSV file via _save_one_of with Pipe delimiter must produce a
    pipe-separated file; the header row must contain | characters.

    This is the primary delimiter test: JSONL and XLSX files in the grid view
    are forced through save-as (they cannot save in-place), and the delimiter
    and quotechar selection in SaveCsvToDialog is the main control the user has
    over the output format.
    """
    path = _examples(main, "first steps", "test.csv")
    viewer = _open_and_wait(qtbot, main, path)
    assert isinstance(viewer, DataViewer)

    output = os.path.join(main.state.cwd, "out_pipe.psv")
    viewer._save_one_of(
        path=output,
        delimiter="Pipe",
        quotechar="Double quotes",
        exts=["csv", "psv"],
    )

    assert os.path.isfile(output), f"Expected pipe-delimited output at: {output}"
    with open(output) as f:
        first_line = f.readline()
    assert "|" in first_line, "Pipe-delimited output must contain | in header"
    assert "," not in first_line.replace('"', ""), (
        "Pipe-delimited output header must not contain unquoted commas"
    )

#chked
def test_csv_save_as_single_quote_quotechar(qtbot, main):
    """
    Saving a CSV that contains values with commas via _save_one_of with
    quotechar='single-quotes' must produce a file where those values are
    wrapped in single-quote characters rather than double quotes.

    DataViewer.QUOTECHARS maps 'single-quotes' → "'", so any value that
    requires quoting (e.g. a value containing the delimiter) will be wrapped
    in single quotes in the output.
    """
    src = os.path.join(main.state.cwd, "needs_quoting.csv")
    with open(src, "w") as f:
        f.write('a,b\n"hello,world",foo\n')

    viewer = _open_and_wait(qtbot, main, src)
    assert isinstance(viewer, DataViewer)

    output = os.path.join(main.state.cwd, "out_single_quote.csv")
    viewer._save_one_of(
        path=output,
        delimiter="Comma",
        quotechar="single-quotes",
        exts=["csv"],
    )

    assert os.path.isfile(output), f"Expected single-quote output at: {output}"
    with open(output) as f:
        content = f.read()
    assert "'" in content, "Output with quotechar='single-quotes' must contain single-quote characters"

#chked
def test_single_quote_csv_displays_correctly_after_toolbar_switch(qtbot, main):
    """
    A CSV saved with single-quote quotechar must display incorrectly when the
    toolbar is set to the default double-quote, then correctly after switching
    the toolbar quotechar to 'Single-quotes'.

    File content: a,b / 'hello,world',foo
    The value 'hello,world' is a single field quoted with single-quotes.

    With double-quote quotechar (default):
      csv.reader does not treat ' as a quote character, so the comma inside
      'hello,world' is treated as a field delimiter.  The data row splits into
      three fields: "'hello", "world'", "foo".  TableModel.columnCount() uses
      max(len(row) for row in data), so it returns 3 — more than the header's 2.

    With single-quote quotechar:
      csv.reader strips the single quotes and preserves the comma as part of the
      field value.  The data row is ["hello,world", "foo"] — 2 fields matching
      the header.  columnCount() returns 2.

    This test guards against a regression where switching the toolbar quotechar
    does not trigger a file reload or does not propagate to the worker, leaving
    a single-quoted CSV permanently misrendered for the user.
    """
    src = os.path.join(main.state.cwd, "single_quoted.csv")
    with open(src, "w") as f:
        f.write("a,b\n'hello,world',foo\n")

    viewer = _open_and_wait(qtbot, main, src)
    assert isinstance(viewer, DataViewer)

    # Default toolbar quotechar is double-quote; the single-quoted field splits
    # on the embedded comma producing 3 columns instead of 2.
    assert viewer.table_view.model().columnCount() == 3, (
        "With double-quote quotechar the embedded comma must split 'hello,world' "
        "into two fields, giving columnCount 3"
    )

    # Switch toolbar to single-quote and trigger a reload
    original_model = viewer.table_view.model()
    sq_index = main.content.toolbar.quotechar.findText(DataConst.SINGLE_QUOTES)
    assert sq_index != -1, "Single-quotes option must exist in the quotechar combo"
    main.content.toolbar.quotechar.setCurrentIndex(sq_index)
    main.content.toolbar.quotechar.activated.emit(sq_index)

    qtbot.waitUntil(
        lambda: viewer.table_view.model() is not original_model,
        timeout=TIMEOUT,
    )

    assert viewer.table_view.model().columnCount() == 2, (
        "With single-quote quotechar 'hello,world' must be treated as one field, "
        "giving columnCount 2"
    )

# ---------------------------------------------------------------------------
# Tests — JSONL in grid view forces save-as
# ---------------------------------------------------------------------------


#chked
def test_jsonl_grid_save_redirects_to_csv(monkeypatch, qtbot, main):
    """
    Calling on_save() on a JSONL file open in the DataViewer must redirect to
    on_save_as(), which shows SaveCsvToDialog.  The dialog is monkeypatched to
    immediately call _save_one_of() so the full write path executes and the
    output CSV can be verified.

    This covers: HOME > save, save-as > jsonl (in grid)
    """
    path = _examples(main, "json", "prompts.jsonl")
    viewer = _open_and_wait(qtbot, main, path)
    assert isinstance(viewer, DataViewer)

    output = os.path.join(main.state.cwd, "prompts_out.csv")
    dialog_shown = []

    class _FakeSaveCsvToDialog:
        def __init__(self, *, parent, main, path):
            self._parent = parent
            dialog_shown.append(path)

        def show(self):
            self._parent._save_one_of(
                path=output,
                delimiter="Comma",
                quotechar="Double quotes",
                exts=["csv"],
            )

    monkeypatch.setattr(
        "flightpath.widgets.panels.data_viewer.SaveCsvToDialog",
        _FakeSaveCsvToDialog,
    )

    viewer.on_save()

    assert len(dialog_shown) == 1, (
        "on_save() on a JSONL file must redirect to SaveCsvToDialog"
    )
    assert os.path.isfile(output), (
        f"Redirected save-as must write a CSV file at: {output}"
    )


# ---------------------------------------------------------------------------
# Tests — JSON in JsonViewer2
# ---------------------------------------------------------------------------

#chked
def test_json_viewer_save_writes_changes(qtbot, main):
    """
    Editing a JSON file in JsonViewer2 and calling _save() must write the
    changed content to disk synchronously.
    """
    path = _examples(main, "named-paths groups", "my_named_paths.json")
    viewer = _open_and_wait(qtbot, main, path)
    assert isinstance(viewer, JsonViewer2)

    viewer.view.setPlainText('{"test_save_marker": true}')
    viewer._save()

    with open(path) as f:
        contents = f.read()
    assert "test_save_marker" in contents, (
        "Saved JSON file must contain the modified content"
    )

#chked
def test_json_viewer_save_as_new_file(qtbot, main):
    """
    Calling _save_as_continue() on a JsonViewer2 with a new path must write
    the current editor content to that path without modifying the original.
    """
    path = _examples(main, "named-paths groups", "my_named_paths.json")
    viewer = _open_and_wait(qtbot, main, path)
    assert isinstance(viewer, JsonViewer2)

    new_path = os.path.join(main.state.cwd, "copy.json")
    viewer._save_as_continue((new_path, True))

    assert os.path.isfile(new_path), f"Save-as must create a new file at: {new_path}"
    with open(new_path) as f:
        contents = f.read()
    assert len(contents) > 0, "Saved-as file must not be empty"

# ---------------------------------------------------------------------------
# Tests — JSONL in JsonViewer2 (Edit as JSON)
# ---------------------------------------------------------------------------

#chked
def test_jsonl_json_viewer_save_preserves_jsonl_format(qtbot, main):
    """
    When a JSONL file is opened via 'Edit as JSON' (JsonViewer2) and saved to
    a .jsonl path via _save_as_continue(), _do_save() must format the output
    as JSONL (one JSON object per line) rather than pretty-printed JSON.

    This is the designated path for editing and saving JSONL content; saving a
    JSONL-derived DataViewer forces save-as to CSV instead.
    """
    path = _examples(main, "json", "prompts.jsonl")
    viewer = _open_as_json_and_wait(qtbot, main, path)
    assert isinstance(viewer, JsonViewer2)

    out_path = os.path.join(main.state.cwd, "prompts_copy.jsonl")
    viewer._save_as_continue((out_path, True))

    assert os.path.isfile(out_path), f"Expected JSONL output at: {out_path}"
    with open(out_path) as f:
        lines = [ln for ln in f.readlines() if ln.strip()]
    assert len(lines) > 1, "JSONL output must have multiple lines (one object per line)"
    import json
    for line in lines:
        json.loads(line)  # each line must be valid JSON


# ---------------------------------------------------------------------------
# Tests — JSON save-as triggers input2 dialog
# ---------------------------------------------------------------------------

#chked
def test_json_viewer_save_as_triggers_input2_dialog(monkeypatch, qtbot, main):
    """
    Calling _save_as() on a JsonViewer2 must invoke meut.input2 to prompt
    the user for a destination path, then write the file when the callback
    is called with ok=True.

    The test stubs input2 to capture its invocation and immediately calls
    the callback with a new path — verifying the full _save_as → _save_as_continue
    → _do_save round-trip in one step.
    """
    path = _examples(main, "named-paths groups", "my_named_paths.json")
    viewer = _open_and_wait(qtbot, main, path)
    assert isinstance(viewer, JsonViewer2)

    input2_calls = []
    new_path = os.path.join(main.state.cwd, "via_dialog.json")

    def fake_input2(*, parent, title, width, msg, text, callback, args=None):
        input2_calls.append(text)
        callback((new_path, True), **(args or {}))

    monkeypatch.setattr(MessageUtility, "input2", fake_input2)

    viewer._save_as()

    assert len(input2_calls) == 1, "_save_as() must invoke input2 exactly once"
    assert os.path.isfile(new_path), f"File must be written after input2 callback: {new_path}"
    with open(new_path) as f:
        contents = f.read()
    assert len(contents) > 0, "File written via save-as dialog must not be empty"


# ---------------------------------------------------------------------------
# Tests — JSON save-as default text and path resolution
# ---------------------------------------------------------------------------

#chked
def test_json_save_as_default_text_is_filename(monkeypatch, qtbot, main):
    """
    _save_as() must pass just the filename (not the directory path) as the
    default text to input2.  Previously it passed os.path.dirname(self.path),
    which defaulted to a directory and caused AttributeError on save.
    """
    path = _examples(main, "named-paths groups", "my_named_paths.json")
    viewer = _open_and_wait(qtbot, main, path)
    assert isinstance(viewer, JsonViewer2)

    captured_text = []

    def fake_input2(*, parent, title, width, msg, text, callback, args=None):
        captured_text.append(text)
        callback(("", False), **(args or {}))  # cancel immediately

    monkeypatch.setattr(MessageUtility, "input2", fake_input2)
    viewer._save_as()

    assert len(captured_text) == 1
    assert captured_text[0] == "my_named_paths.json", (
        "Default text must be the bare filename, not the directory path"
    )
    assert os.sep not in captured_text[0], (
        "Default text must not contain a path separator"
    )


#chked
def test_json_save_as_bare_filename_saves_alongside_original(qtbot, main):
    """
    When _save_as_continue receives a bare filename (no path separator), the
    file must be written next to the original in the same directory.
    """
    path = _examples(main, "named-paths groups", "my_named_paths.json")
    viewer = _open_and_wait(qtbot, main, path)
    assert isinstance(viewer, JsonViewer2)

    viewer._save_as_continue(("sibling_copy.json", True))

    expected = os.path.join(_examples(main, "named-paths groups"), "sibling_copy.json")
    assert os.path.isfile(expected), (
        f"Bare filename must save next to the original; expected: {expected}"
    )


#chked
def test_json_save_as_shows_status_bar_on_success(qtbot, main):
    """
    A successful save-as must display a status-bar message so the user gets
    visible confirmation.
    """
    path = _examples(main, "named-paths groups", "my_named_paths.json")
    viewer = _open_and_wait(qtbot, main, path)
    assert isinstance(viewer, JsonViewer2)

    out = os.path.join(main.state.cwd, "status_bar_check.json")
    viewer._save_as_continue((out, True))

    msg = main.statusBar().currentMessage()
    assert out in msg, (
        f"Status bar must mention the saved path; got: '{msg}'"
    )


# ---------------------------------------------------------------------------
# Tests — JSON save-as error handling (directory path)
# ---------------------------------------------------------------------------

#chked
def test_json_save_as_directory_input_shows_warning(monkeypatch, qtbot, main):
    """
    If the user enters a path that resolves to an existing directory,
    _save_as_continue must call meut.warning2 to notify them.
    Previously this path raised an unhandled exception with no user feedback.
    """
    path = _examples(main, "named-paths groups", "my_named_paths.json")
    viewer = _open_and_wait(qtbot, main, path)
    assert isinstance(viewer, JsonViewer2)

    warnings = []

    def fake_warning2(*, parent, title, msg):
        warnings.append(msg)

    monkeypatch.setattr(MessageUtility, "warning2", fake_warning2)
    # Also stub _save_as so the re-open after warning doesn't try to show input2
    monkeypatch.setattr(viewer, "_save_as", lambda: None)

    # Pass the directory itself as the "name" — simulates the user hitting OK
    # without editing the old default text that was os.path.dirname(self.path)
    dir_path = _examples(main, "named-paths groups")
    viewer._save_as_continue((dir_path, True))

    assert len(warnings) == 1, (
        "Entering a directory path must trigger exactly one warning"
    )
    assert "directory" in warnings[0].lower(), (
        f"Warning message must mention 'directory'; got: '{warnings[0]}'"
    )


#chked
def test_json_save_as_directory_input_reopens_dialog(monkeypatch, qtbot, main):
    """
    After showing a warning for a directory path, _save_as_continue must
    re-invoke _save_as() so the user gets another chance to enter a valid name.
    """
    path = _examples(main, "named-paths groups", "my_named_paths.json")
    viewer = _open_and_wait(qtbot, main, path)
    assert isinstance(viewer, JsonViewer2)

    monkeypatch.setattr(MessageUtility, "warning2", lambda **kw: None)
    reopen_calls = []
    monkeypatch.setattr(viewer, "_save_as", lambda: reopen_calls.append(1))

    dir_path = _examples(main, "named-paths groups")
    viewer._save_as_continue((dir_path, True))

    assert len(reopen_calls) == 1, (
        "_save_as() must be called once after a directory-path warning"
    )
