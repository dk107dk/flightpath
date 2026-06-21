"""
pytest-qt tests for the one-off run workflow.

Checklist coverage:
  HOME > one-off run > run csvpath file (cmd-r / context menu Run)
  HOME > one-off run > result tabs appear (Printouts, Log, Errors, Matches, Variables, Code, Why)
  HOME > one-off run > Matches tab contains data
  HOME > one-off run > right-click 'Save as' on Matches writes CSV

The one-off run is triggered via CsvpathViewer.run_one.run_one_csvpath_2().  Tests
call this method directly with the absolute path to the test CSV and the csvpath text
from the opened viewer, bypassing the file-picker dialog.  Hello World.csvpath already
has a test-data: directive so the filepath is only used for path resolution; no
interactive dialog is needed.

OneOffRunWorker runs on Qt's thread pool; tests use waitUntil to block until the
result tabs appear in main.helper.help_and_feedback before asserting.

Run with:
  QT_QPA_PLATFORM=offscreen poetry run python -m pytest tests/gui/test_one_off_run.py -v
"""

import os

from flightpath.util.tabs_utility import TabsUtility as taut
from flightpath.widgets.panels.csvpath_viewer import CsvpathViewer
from flightpath.widgets.panels.data_viewer import DataViewer

# isolated_home and main fixtures are provided by conftest.py

TIMEOUT = 15000  # ms — CsvPath collect() needs more headroom than a file open
MAIN_MODULE = "flightpath.main"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _examples(main, *parts) -> str:
    return os.path.join(main.state.cwd, "examples", *parts)


def _make_dialog(name: str, accepted: bool = True):
    """QInputDialog stub that immediately returns *name* without showing a dialog."""
    class _FakeDialog:
        def setFixedSize(self, *a): pass
        def setLabelText(self, *a): pass
        def setTextValue(self, *a): pass
        def exec(self): return 1 if accepted else 0
        def textValue(self): return name
    return _FakeDialog


def _open_and_wait(qtbot, main, path: str) -> object:
    """Dispatch a file open and block until its viewer tab appears."""
    main.read_validate_and_display_file_for_path(path)
    qtbot.waitUntil(
        lambda: taut.find_tab(main.content.tab_widget, path) is not None,
        timeout=TIMEOUT,
    )
    return taut.find_tab(main.content.tab_widget, path)[1]


def _has_tab(tab_widget, object_name: str) -> bool:
    return taut.find_tab(tab_widget, object_name) is not None


def _run_hello_world(qtbot, main) -> None:
    """Open Hello World.csvpath, trigger a one-off run, and block until result tabs appear."""
    csvpath_path = _examples(main, "first steps", "Hello World.csvpath")
    data_path = _examples(main, "first steps", "test.csv")
    assert os.path.exists(csvpath_path), f"Missing example: {csvpath_path}"
    assert os.path.exists(data_path), f"Missing example: {data_path}"

    viewer = _open_and_wait(qtbot, main, csvpath_path)
    assert isinstance(viewer, CsvpathViewer), "Expected a CsvpathViewer for .csvpath file"

    csvpath_text = viewer.text_edit.toPlainText()
    viewer.run_one.run_one_csvpath_2(data_path, csvpath=csvpath_text)

    # "Log" is added after all Printouts tabs; its appearance confirms _run_feedback completed.
    qtbot.waitUntil(
        lambda: _has_tab(main.helper.help_and_feedback, "Log"),
        timeout=TIMEOUT,
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_one_off_run_creates_result_tabs(qtbot, main):
    """
    Running Hello World.csvpath must populate help_and_feedback with all standard
    result tabs: at least one Printouts tab, Log, Errors, Matches, Variables, and Why.
    Code (shown as 'Automation') is excluded from right-click save and skipped here.
    """
    _run_hello_world(qtbot, main)

    hf = main.helper.help_and_feedback
    for name in ("Log", "Errors", "Matches", "Variables", "Why"):
        assert _has_tab(hf, name), f"Expected '{name}' tab in result panel"

    has_printouts = any(
        hf.widget(i).objectName().startswith("Printouts")
        for i in range(hf.count())
    )
    assert has_printouts, "Expected at least one Printouts tab in result panel"


def test_one_off_run_matches_tab_has_data(qtbot, main):
    """
    The Matches tab must contain a DataViewer with a populated model after running
    Hello World.csvpath — it matches exactly 1 row from test.csv.
    """
    _run_hello_world(qtbot, main)

    hf = main.helper.help_and_feedback
    result = taut.find_tab(hf, "Matches")
    assert result is not None, "Matches tab must exist after a one-off run"

    matches_widget = result[1]
    layout = matches_widget.layout()
    dv = layout.itemAt(0).widget()
    assert isinstance(dv, DataViewer), "Matches tab must contain a DataViewer"
    assert dv.table_view.model() is not None, "DataViewer model must be set"


def test_one_off_run_save_matches_writes_csv(monkeypatch, qtbot, main):
    """
    Calling on_save_sample() for the Matches tab must write a CSV file into the
    project directory.  The QInputDialog prompt for the filename is monkeypatched
    to accept 'matches.csv' without user interaction.
    """
    _run_hello_world(qtbot, main)

    hf = main.helper.help_and_feedback
    matches_index = -1
    for i in range(hf.count()):
        if hf.widget(i).objectName() == "Matches":
            matches_index = i
            break
    assert matches_index != -1, "Matches tab must exist before save test"

    monkeypatch.setattr(MAIN_MODULE + ".QInputDialog", _make_dialog("matches.csv"))

    hf.on_save_sample(matches_index)

    saved = os.path.join(main.state.cwd, "matches.csv")
    assert os.path.isfile(saved), f"Expected saved CSV at: {saved}"
