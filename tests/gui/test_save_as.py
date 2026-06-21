"""
pytest-qt tests for save and save-as across all content viewer types.

Checklist coverage:
  HOME > save, save-as > csvpath
  HOME > save, save-as > json
  HOME > save, save-as > jsonl (in JsonViewer2)
  HOME > save, save-as > grid (CSV)
  HOME > delimiters > save data as new delimiter
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


def test_csvpath_save_writes_changes(qtbot, main):
    """
    Editing a csvpath file and pressing save (CsvPathTextEdit.on_save) must
    write the changed text to disk synchronously.
    """
    path = _examples(main, "first steps", "Hello World.csvpath")
    viewer = _open_and_wait(qtbot, main, path)
    assert isinstance(viewer, CsvpathViewer)

    viewer.text_edit.appendPlainText("~ test-save-marker")
    viewer.text_edit.on_save()

    with open(path) as f:
        contents = f.read()
    assert "test-save-marker" in contents, (
        "Saved csvpath file must contain the appended text"
    )


# ---------------------------------------------------------------------------
# Tests — CSV grid save-as with delimiter
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Tests — JSONL in grid view forces save-as
# ---------------------------------------------------------------------------


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
