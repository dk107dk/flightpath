"""
pytest-qt tests for the Find Data dialog (FindFileByReferenceDialog).

Checklist coverage:
  DIALOGS > find data > find files — search returns matching named-file entries
  DIALOGS > find data > find results — search returns matching archive entries
  DIALOGS > find data > show metadata and data — clicking a result opens a content tab
  DIALOGS > find data > welcome page "Find data" button opens dialog without error

== Dialog overview ==

FindFileByReferenceDialog is a non-blocking dialog that lets the user search
named-files (registered data inputs) and named-results (archive run outputs)
using a structured reference syntax: $name.datatype.query.

Controls:
  datatype — QComboBox: "...", "files", "results"
  named_x_name — QComboBox: populated after datatype is selected with file/result names
  name_one — QLineEdit: the query segment (defaults to ":all" on first pick)
  table_view / model — QTableView / QStandardItemModel (2-col: Date, Path)
  results_description — QLabel: "<n> named-{datatype} found with reference {r}"

Flow: pick datatype → _on_pick_datatype() populates named_x_name → pick name →
_on_pick_name() resolves reference → add_data() fills table.

Both _on_pick_datatype and _on_pick_name are connected to activated (user
interaction) signals.  Tests call them directly without going through show_dialog()
(which calls exec() and blocks).

== FileActivationListener note ==

Tests that call add_named_file() immediately before constructing a dialog must
patch FileActivationListener.metadata_update to prevent a background thread from
starting.  That thread creates a fresh CsvPaths() and parses a Lark grammar;
when this races Qt's proxy-model filterAcceptsRow() during dialog widget
construction a segfault results.  See memory/project_activation_listener_bugs.md.

Tests that call _setup_and_run() do not need the patch because the waitUntil
for the Log tab gives the Lark parsing thread time to finish before Qt processes
further events.

Run with:
  QT_QPA_PLATFORM=offscreen poetry run python -m pytest tests/gui/test_find_data.py -v
"""

import os

from csvpath.managers.files.files_activation_listener import FileActivationListener

from flightpath.dialogs.find_file_by_reference_dialog import FindFileByReferenceDialog
from flightpath.dialogs.reference_files.reference_file_handler import ReferenceFileHandler
from flightpath.util.tabs_utility import TabsUtility as taut

# isolated_home and main fixtures are provided by conftest.py

TIMEOUT = 20000


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _examples(main, *parts) -> str:
    return os.path.join(main.state.cwd, "examples", *parts)


def _register_named_file(main, name: str = "test") -> str:
    csv_file = _examples(main, "first steps", "test.csv")
    main.csvpaths.config.set(section="inputs", name="allow_local_files", value=True)
    main.csvpaths.file_manager.add_named_file(name=name, path=csv_file, template=None)
    return name


def _setup_and_run(qtbot, main) -> None:
    """Register test named-file and hello-world named-paths, run collect_paths."""
    csvpath_file = _examples(main, "first steps", "Hello World.csvpath")
    csv_file = _examples(main, "first steps", "test.csv")
    csvpaths = main.csvpaths
    csvpaths.config.set(section="inputs", name="allow_local_files", value=True)
    csvpaths.file_manager.add_named_file(name="test", path=csv_file, template=None)
    csvpaths.paths_manager.add_named_paths_from_file(
        name="hello-world", file_path=csvpath_file, template=None, append=False
    )
    main.run_paths(
        method="collect_paths",
        named_paths_name="hello-world",
        named_file_name="test",
        template=None,
    )
    qtbot.waitUntil(
        lambda: any(
            main.helper.help_and_feedback.widget(i).objectName().startswith("Log-")
            for i in range(main.helper.help_and_feedback.count())
        ),
        timeout=TIMEOUT,
    )


def _open_find_dialog(qtbot, main) -> FindFileByReferenceDialog:
    dialog = FindFileByReferenceDialog(main=main)
    qtbot.addWidget(dialog)
    return dialog


def _populate_files(dialog, name: str = "test") -> None:
    """Select 'files' datatype and the given named-file; fire _on_pick_name."""
    dialog.datatype.setCurrentIndex(1)  # "files"
    dialog._on_pick_datatype()
    idx = dialog.named_x_name.findText(name)
    dialog.named_x_name.setCurrentIndex(idx)
    dialog._on_pick_name()


def _populate_results(dialog, name: str = "hello-world") -> None:
    """Select 'results' datatype and the given named-result; fire _on_pick_name."""
    dialog.datatype.setCurrentIndex(2)  # "results"
    dialog._on_pick_datatype()
    idx = dialog.named_x_name.findText(name)
    dialog.named_x_name.setCurrentIndex(idx)
    dialog._on_pick_name()


# ---------------------------------------------------------------------------
# Tests — find files
# ---------------------------------------------------------------------------


def test_find_files_populates_table(monkeypatch, qtbot, main):
    """
    Selecting 'files' datatype and a registered named-file must populate the
    results table with at least one row.

    The dialog resolves reference $test.files.:all via FilesReferenceFinder and
    calls add_data() to fill the QStandardItemModel.  The results_description
    label must report the count and mention 'named-files'.

    FileActivationListener.metadata_update is suppressed to prevent the Lark
    grammar race described in the module docstring.
    """
    monkeypatch.setattr(FileActivationListener, "metadata_update", lambda self, mdata: None)

    _register_named_file(main)
    dialog = _open_find_dialog(qtbot, main)
    _populate_files(dialog)

    assert dialog.model.rowCount() > 0, (
        "Results table must have at least one row after searching with ':all'"
    )
    assert "named-files" in dialog.results_description.text(), (
        f"results_description must mention 'named-files'; got: {dialog.results_description.text()!r}"
    )


def test_find_files_table_has_date_and_path_columns(monkeypatch, qtbot, main):
    """
    The results table must have two columns: Date (col 0) and Path (col 1).

    Column 1 must contain a non-empty path string that ends with the registered
    data file's name.  Column 0 may be empty if no manifest timestamp exists.
    """
    monkeypatch.setattr(FileActivationListener, "metadata_update", lambda self, mdata: None)

    _register_named_file(main)
    dialog = _open_find_dialog(qtbot, main)
    _populate_files(dialog)

    assert dialog.model.columnCount() == 2, "Model must have exactly 2 columns"
    path_item = dialog.model.item(0, 1)
    assert path_item is not None, "Row 0 column 1 (Path) must exist"
    path = path_item.text()
    assert path and os.path.exists(path), (
        f"Path column must contain an existing file path; got {path!r}"
    )


# ---------------------------------------------------------------------------
# Tests — find results
# ---------------------------------------------------------------------------


def test_find_results_populates_table(qtbot, main):
    """
    After a production run, selecting 'results' datatype and the named-paths
    group name must populate the table with archive run entries.

    The dialog resolves reference $hello-world.results.:all via
    ResultsReferenceFinder and calls add_data() to fill the model.

    _setup_and_run uses waitUntil (Log tab), which gives the FileActivationListener
    thread time to finish before Qt processes further events — no extra patch needed.
    """
    _setup_and_run(qtbot, main)
    dialog = _open_find_dialog(qtbot, main)
    _populate_results(dialog)

    assert dialog.model.rowCount() > 0, (
        "Results table must have at least one row after a production run"
    )
    assert "named-results" in dialog.results_description.text(), (
        f"results_description must mention 'named-results'; got: {dialog.results_description.text()!r}"
    )


# ---------------------------------------------------------------------------
# Tests — open data file from result row
# ---------------------------------------------------------------------------


def test_open_files_file_opens_content_tab(monkeypatch, qtbot, main):
    """
    ReferenceFileHandler._open_files_file() must open the named-file's data file
    in a content viewer tab.

    After the table is populated, the path for row 0 is read from column 1 of
    the model and passed to read_validate_and_display_file_for_path().  A matching
    content tab (objectName == path) must appear.

    This exercises the "show metadata and data" flow: clicking a row in the find-
    files table opens the underlying CSV in the DataViewer.
    """
    monkeypatch.setattr(FileActivationListener, "metadata_update", lambda self, mdata: None)

    _register_named_file(main)
    dialog = _open_find_dialog(qtbot, main)
    _populate_files(dialog)

    assert dialog.model.rowCount() > 0, "Precondition: table must have at least one row"

    handler = ReferenceFileHandler(main=main, parent=dialog)
    path = handler._item(0)
    handler._open_files_file(0)

    qtbot.waitUntil(
        lambda: taut.find_tab(main.content.tab_widget, path) is not None,
        timeout=TIMEOUT,
    )


# ---------------------------------------------------------------------------
# Tests — welcome page "Find data" button
# ---------------------------------------------------------------------------


def test_welcome_find_data_button_disabled_on_empty_project(main):
    """
    The welcome page 'Find data' button must be disabled when no named-files or
    named-results exist.

    update_find_data_button() checks file_manager.named_files_count and
    results_manager.list_named_results(); if both are zero the button is disabled.
    """
    assert not main.welcome.button_find_data.isEnabled(), (
        "Find data button must be disabled on a fresh project with no named data"
    )


def test_welcome_find_data_button_enabled_after_registration(monkeypatch, qtbot, main):
    """
    The welcome page 'Find data' button must become enabled after a named-file
    is registered.

    Registering a file increments named_files_count above zero.  The sidebar
    calls update_find_data_button() after registration; the test calls it
    explicitly since we bypass the full registration UI flow.
    """
    monkeypatch.setattr(FileActivationListener, "metadata_update", lambda self, mdata: None)

    _register_named_file(main)
    main.welcome.update_find_data_button()

    assert main.welcome.button_find_data.isEnabled(), (
        "Find data button must be enabled after at least one named-file is registered"
    )


def test_welcome_find_data_button_opens_dialog(monkeypatch, qtbot, main):
    """
    Clicking the welcome page 'Find data' button must construct a
    FindFileByReferenceDialog and pass it to show_now_or_later.

    on_click_find_data() creates the dialog and calls main.show_now_or_later(find).
    The test monkeypatches show_now_or_later to capture the call and verify the
    dialog type — without ever showing a blocking dialog window.

    Non-dialog showables (e.g. the howto QTextEdit created inside the dialog's
    __init__) are still passed through to the original show_now_or_later so
    widget visibility is not broken.
    """
    monkeypatch.setattr(FileActivationListener, "metadata_update", lambda self, mdata: None)

    _register_named_file(main)
    main.welcome.update_find_data_button()

    shown = []
    original_show = main.show_now_or_later

    def _capture(showable):
        shown.append(showable)
        if not isinstance(showable, FindFileByReferenceDialog):
            original_show(showable)

    monkeypatch.setattr(main, "show_now_or_later", _capture)

    main.welcome.on_click_find_data()

    dialogs = [s for s in shown if isinstance(s, FindFileByReferenceDialog)]
    assert len(dialogs) == 1, (
        f"Exactly one FindFileByReferenceDialog must be passed to show_now_or_later; "
        f"got {len(dialogs)} (total shown: {len(shown)})"
    )
