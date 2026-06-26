"""
pytest-qt tests for the Stage Data and Load Csvpaths dialog flows.

Checklist coverage:
  DIALOGS > stage data > stage a single file
  DIALOGS > stage data > stage a directory
  DIALOGS > load csvpaths > load from a .csvpath / .csvpaths file
  DIALOGS > load csvpaths > load from a directory of csvpath files
  DIALOGS > load csvpaths > load from a JSON definition file (when well-formed)
  DIALOGS > load csvpaths > load from malformed JSON — errors show in errors form
  DIALOGS > load csvpaths > overwrite existing definition (copy-back flow)
  DIALOGS > load csvpaths > definition.json is pretty-printed after loading from JSON
  DIALOGS > load csvpaths > copy-back of definition.json from named-paths sidebar preserves pretty-printing

== Stage Data flow ==

StageDataDialog(main, path, parent=sidebar) is opened via sidebar_actions._stage_data().
sidebar.stage_dialog is set to the dialog instance before show_dialog() is called.
The "Stage" button calls sidebar.do_stage(), which reads fields from sidebar.stage_dialog
and calls either:
  - file_manager.add_named_file(name, path, template)    — for a single file
  - file_manager.add_named_files_from_dir(name, dirname) — for a directory

Tests bypass show_dialog() (which calls exec()) and call do_stage() directly after
setting sidebar.stage_dialog and populating form fields.

After do_stage() the dialog is closed and deleted (stage_dialog = None), so widgets
must not be accessed after that point.

== Load Csvpaths flow ==

CsvpathLoader is the controller; LoadPathsDialog is the view.
  loader.load_paths(path) creates the dialog and shows it.
  The "Create"/"Overwrite" button calls loader.do_overwrite_named_paths_load() →
    do_load() → do_load_file() / do_load_dir() / do_load_json() by extension.
  _do_load_file() and _do_load_dir_answer() do the actual registration and then
  call _delete_load_dialog(), so the dialog is gone after a successful load.

Tests construct the loader and dialog directly, set loader.load_dialog = dialog, and
call the internal load methods directly to avoid show_dialog() / exec().

== FileActivationListener note ==

add_named_file() fires a metadata event that starts FileActivationListener's background
thread. Tests that call add_named_file() (Stage Data tests) monkeypatch it away.
add_named_paths_from_file/dir/json do not trigger FileActivationListener, so those
tests do not need the patch.

Run with:
  QT_QPA_PLATFORM=offscreen poetry run python -m pytest tests/gui/test_stage_and_load.py -v
"""

import json
import os

from PySide6.QtWidgets import QMessageBox

from csvpath.managers.files.files_activation_listener import FileActivationListener

from flightpath.actions.csvpath_loader import CsvpathLoader
from flightpath.dialogs.load_paths_dialog import LoadPathsDialog
from flightpath.dialogs.stage_data_dialog import StageDataDialog
from flightpath.util.editable import EditStates
from flightpath.util.tabs_utility import TabsUtility as taut
from flightpath.widgets.panels.json_viewer_2 import JsonViewer2

# isolated_home and main fixtures are provided by conftest.py

TIMEOUT = 8000  # ms


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _examples(main, *parts) -> str:
    return os.path.join(main.state.cwd, "examples", *parts)


# ---------------------------------------------------------------------------
# Stage Data tests
# ---------------------------------------------------------------------------


def test_stage_single_file_registers_named_file(monkeypatch, qtbot, main):
    """
    Staging a single CSV file via StageDataDialog must register it as a
    named-file accessible to the framework.

    do_stage() reads the file path from dialog.path and the name from
    named_file_name_ctl, then calls file_manager.add_named_file().  After
    do_stage() the dialog is closed and stage_dialog is set to None by the
    sidebar; the test only checks framework state, not widget state.

    FileActivationListener.metadata_update is suppressed to prevent the
    Lark-grammar background thread from racing Qt's proxy model.  See
    memory/project_activation_listener_bugs.md.
    """
    monkeypatch.setattr(FileActivationListener, "metadata_update", lambda self, mdata: None)

    csv_file = _examples(main, "first steps", "test.csv")
    assert os.path.exists(csv_file), f"Test CSV not found at: {csv_file}"

    dialog = StageDataDialog(main=main, path=csv_file, parent=main.sidebar)
    main.sidebar.stage_dialog = dialog

    dialog.named_file_name_ctl.setText("staged-single")
    main.sidebar.do_stage()

    fm = main.csvpaths.file_manager
    assert fm.has_named_file("staged-single"), (
        "Stage Data must register the file under the given named-file name"
    )
    assert fm.named_files_count >= 1, (
        "named_files_count must be at least 1 after staging"
    )


def test_stage_single_file_sidebar_refreshes(monkeypatch, qtbot, main):
    """
    After do_stage() succeeds, the named-files sidebar (sidebar_rt_top) must be
    rebuilt as a new SidebarNamedFiles widget.

    do_stage() calls main.rt_col.replaceWidget(0, SidebarNamedFiles(...)) at the
    end of a successful stage.  The test verifies that sidebar_rt_top is not None
    and is a QWidget (the new tree), confirming the refresh completed.
    """
    monkeypatch.setattr(FileActivationListener, "metadata_update", lambda self, mdata: None)

    csv_file = _examples(main, "first steps", "test.csv")
    dialog = StageDataDialog(main=main, path=csv_file, parent=main.sidebar)
    main.sidebar.stage_dialog = dialog
    dialog.named_file_name_ctl.setText("staged-sidebar-test")

    main.sidebar.do_stage()

    assert main.sidebar_rt_top is not None, (
        "sidebar_rt_top must be rebuilt (non-None) after do_stage()"
    )


def test_stage_directory_with_regex_registers_only_matching_file(monkeypatch, tmp_path, main):
    """
    Staging a directory with a regex in regex_ctl must register only the files
    whose paths match the regex, not all files in the directory.

    Bug: do_stage() checked hasattr(dialog, "regex") instead of
    hasattr(dialog, "regex_ctl"), so regex was always None and every file in
    the directory was registered regardless of the pattern.

    Fix: the hasattr check now uses "regex_ctl", so regex is read correctly
    and passed to add_named_files_from_dir(), which skips non-matching files.
    """
    monkeypatch.setattr(FileActivationListener, "metadata_update", lambda self, mdata: None)

    (tmp_path / "alpha.csv").write_text("id,value\n1,a\n")
    (tmp_path / "beta.csv").write_text("id,value\n2,b\n")

    dialog = StageDataDialog(main=main, path=str(tmp_path), parent=main.sidebar)
    main.sidebar.stage_dialog = dialog

    dialog.separate_ctl.setChecked(True)
    dialog.regex_ctl.setText("alpha")

    main.sidebar.do_stage()

    fm = main.csvpaths.file_manager
    assert fm.has_named_file("alpha"), (
        "Regex 'alpha' must match alpha.csv and register it as a named-file"
    )
    assert not fm.has_named_file("beta"), (
        "Regex 'alpha' must not match beta.csv; beta must not be registered"
    )


def test_stage_directory_registers_multiple_named_files(monkeypatch, qtbot, main):
    """
    Staging a directory with 'separate named-files' checked must register each
    CSV/data file found in that directory as its own named-file.

    With separate_ctl=True (the default), add_named_files_from_dir() is called
    with name=None, which derives each named-file name from the individual
    file's stem.  The 'first steps' example directory contains test.csv so at
    least one named-file must be registered.

    FileActivationListener.metadata_update is suppressed for the same reason as
    the single-file test.
    """
    monkeypatch.setattr(FileActivationListener, "metadata_update", lambda self, mdata: None)

    examples_dir = _examples(main, "first steps")
    assert os.path.isdir(examples_dir), f"Examples dir not found: {examples_dir}"

    dialog = StageDataDialog(main=main, path=examples_dir, parent=main.sidebar)
    main.sidebar.stage_dialog = dialog

    # separate_ctl is True by default — each file gets its own name
    assert dialog.separate_ctl.isChecked(), "separate_ctl must default to checked"
    # do NOT set named_file_name_ctl — it's disabled and auto-set when separate

    main.sidebar.do_stage()

    fm = main.csvpaths.file_manager
    assert fm.named_files_count >= 1, (
        "At least one named-file must be registered after staging a directory "
        f"that contains data files; got count={fm.named_files_count}"
    )


# ---------------------------------------------------------------------------
# Load Csvpaths tests — helpers
# ---------------------------------------------------------------------------


def _make_loader_and_dialog(main, path: str) -> tuple[CsvpathLoader, LoadPathsDialog]:
    """
    Create a CsvpathLoader and LoadPathsDialog for the given path and wire
    them together (loader.load_dialog = dialog).  The caller owns both objects
    and must NOT call show_dialog() or exec().
    """
    loader = CsvpathLoader(main=main, parent=main.sidebar)
    dialog = LoadPathsDialog(
        main=main, path=path, parent=main.sidebar, loader=loader
    )
    loader.load_dialog = dialog
    return loader, dialog


# ---------------------------------------------------------------------------
# Load Csvpaths tests
# ---------------------------------------------------------------------------


def test_load_csvpath_file_creates_named_paths_group(qtbot, main):
    """
    Loading a .csvpath file via CsvpathLoader must register it as a named-paths
    group accessible to the framework.

    do_load_file(overwrite=True) sets allow_local_files, then calls
    paths_manager.add_named_paths_from_file(name, file_path, template, append=False).
    After a successful load, _delete_load_dialog() closes the dialog, so only
    framework state is checked.
    """
    csvpath_file = _examples(main, "first steps", "Hello World.csvpath")
    loader, dialog = _make_loader_and_dialog(main, csvpath_file)
    dialog.named_paths_name_ctl.setText("hello-world")

    loader.do_load_file(overwrite=True)

    pm = main.csvpaths.paths_manager
    assert pm.has_named_paths("hello-world"), (
        "do_load_file must register the named-paths group under the given name"
    )


def test_load_csvpath_file_with_template_stores_template(qtbot, main):
    """
    Loading a .csvpath file with a template must persist the template for the
    named-paths group.

    do_load_file() passes the template_ctl text to add_named_paths_from_file().
    The template is stored via paths_manager.describer and retrievable by
    get_template().
    """
    csvpath_file = _examples(main, "first steps", "Hello World.csvpath")
    loader, dialog = _make_loader_and_dialog(main, csvpath_file)
    dialog.named_paths_name_ctl.setText("hello-world-tmpl")
    dialog.template_ctl.setText("results/:run_dir")

    loader.do_load_file(overwrite=True)

    pm = main.csvpaths.paths_manager
    assert pm.has_named_paths("hello-world-tmpl"), (
        "Named-paths group must be registered before template can be retrieved"
    )
    stored = pm.describer.get_template("hello-world-tmpl")
    assert stored == "results/:run_dir", (
        f"Template must be stored and retrievable; got {stored!r}"
    )


def test_load_csvpaths_directory_creates_named_paths_group(qtbot, main):
    """
    Loading a directory of .csvpath files must register them all as a single
    named-paths group.

    do_load_dir() calls paths_manager.add_named_paths_from_dir(name, directory)
    which scans for csvpath-extension files and registers them all under the
    given group name.  The 'first steps' directory has two .csvpath files so
    the group should contain at least one path.
    """
    examples_dir = _examples(main, "first steps")
    loader, dialog = _make_loader_and_dialog(main, examples_dir)
    dialog.named_paths_name_ctl.setText("first-steps-group")

    loader.do_load_dir(overwrite=True)

    pm = main.csvpaths.paths_manager
    assert pm.has_named_paths("first-steps-group"), (
        "do_load_dir must register all csvpath files in the directory under the given name"
    )


def test_load_json_definition_creates_named_paths_groups(monkeypatch, qtbot, tmp_path, main):
    """
    Loading a well-formed JSON definition file must register all named-paths
    groups it describes.

    do_load_json() calls paths_manager.add_named_paths_from_json(file_path).
    The JSON maps group names to lists of csvpath file paths.  The test creates
    a JSON file with absolute paths so resolution is unambiguous.

    QMessageBox.question is monkeypatched to return Yes, bypassing the blocking
    confirmation dialog that do_load_json() normally shows.
    """
    csvpath_file = _examples(main, "first steps", "Hello World.csvpath")
    json_data = {"from-json-group": [csvpath_file]}
    json_path = tmp_path / "named_paths.json"
    json_path.write_text(json.dumps(json_data))

    loader, dialog = _make_loader_and_dialog(main, str(json_path))
    monkeypatch.setattr(
        QMessageBox,
        "question",
        staticmethod(lambda *a, **kw: QMessageBox.Yes),
    )

    loader.do_load_json()

    pm = main.csvpaths.paths_manager
    assert pm.has_named_paths("from-json-group"), (
        "do_load_json must register each group named in the JSON definition"
    )


def test_load_malformed_json_shows_error(monkeypatch, qtbot, tmp_path, main):
    """
    Loading a malformed JSON file must trigger load_errors() on the dialog
    rather than registering any named-paths groups.

    do_load_json() catches the JSON parse exception and calls
    load_dialog.load_errors(msg, title, errors).  The test monkeypatches
    load_errors to capture the call.  No named-paths group should be registered.

    QMessageBox.question is also monkeypatched since do_load_json() shows a
    confirmation dialog before attempting the load.
    """
    bad_json = tmp_path / "bad.json"
    bad_json.write_text("{not: valid json}")

    loader, dialog = _make_loader_and_dialog(main, str(bad_json))

    monkeypatch.setattr(
        QMessageBox,
        "question",
        staticmethod(lambda *a, **kw: QMessageBox.Yes),
    )

    errors_shown = []
    monkeypatch.setattr(
        dialog,
        "load_errors",
        lambda msg, title, errors: errors_shown.append((msg, title, errors)),
    )

    loader.do_load_json()

    assert len(errors_shown) >= 1, (
        "load_errors must be called when the JSON file is malformed; "
        f"got {len(errors_shown)} calls"
    )
    assert main.csvpaths.paths_manager.named_paths_count == 0, (
        "No named-paths group must be registered after a failed JSON load"
    )


def test_load_dialog_shows_overwrite_button_for_existing_name(qtbot, main):
    """
    When named_paths_name_ctl is set to an already-registered group name,
    _name_check() must enable the 'Append' button and change the 'Create'
    button to 'Overwrite'.

    This is the gate that guards the overwrite flow: the user sees 'Overwrite'
    and knows they are replacing an existing definition.  The test registers
    'hello-world' first, then opens a fresh dialog for the same file and sets
    the name to 'hello-world'.
    """
    # Pre-register the group
    csvpath_file = _examples(main, "first steps", "Hello World.csvpath")
    main.csvpaths.paths_manager.add_named_paths_from_file(
        name="hello-world", file_path=csvpath_file, template=None, append=False
    )
    assert main.csvpaths.paths_manager.has_named_paths("hello-world"), (
        "Precondition: hello-world must be registered before the dialog test"
    )

    loader, dialog = _make_loader_and_dialog(main, csvpath_file)
    qtbot.addWidget(dialog)

    dialog.named_paths_name_ctl.setText("hello-world")
    dialog._name_changed()  # triggers _check_for_template + _name_check

    assert dialog.load_button.text() == "Overwrite", (
        f"Load button must read 'Overwrite' when name already exists; "
        f"got {dialog.load_button.text()!r}"
    )
    assert dialog.append_button.isEnabled(), (
        "Append button must be enabled when the group name already exists"
    )


def test_overwrite_existing_named_paths_succeeds(qtbot, main):
    """
    Re-loading a .csvpath file under an existing group name must succeed and
    the group must remain registered.

    _do_load_file(QMessageBox.Yes, overwrite=True, ...) is called directly to
    bypass the yesNo confirmation dialog that do_load_file() normally shows
    when the name already exists.  This exercises the core 'copy-back' flow
    where a modified csvpath file is re-registered.
    """
    csvpath_file = _examples(main, "first steps", "Hello World.csvpath")

    # First registration
    main.csvpaths.paths_manager.add_named_paths_from_file(
        name="hello-world", file_path=csvpath_file, template=None, append=False
    )

    # Second registration (overwrite) via the loader's internal slot
    loader, dialog = _make_loader_and_dialog(main, csvpath_file)
    dialog.named_paths_name_ctl.setText("hello-world")

    loader._do_load_file(
        QMessageBox.Yes,
        overwrite=True,
        named_paths_name="hello-world",
        paths=main.csvpaths,
        template=None,
    )

    pm = main.csvpaths.paths_manager
    assert pm.has_named_paths("hello-world"), (
        "Named-paths group must still be registered after overwrite"
    )


def _named_paths_root(main) -> str:
    return main.csvpath_config.get(section="inputs", name="csvpaths")


# ---------------------------------------------------------------------------
# Load Csvpaths from directory — error handling tests
# ---------------------------------------------------------------------------


def test_load_dir_with_no_csvpath_files_shows_warning(monkeypatch, tmp_path, main):
    """
    Loading a directory that contains no files with csvpath extensions must
    show a warning dialog instead of crashing with a TypeError.

    Bug: _do_load_dir_answer called self.load_dialog.warning(callback=...) but
    LoadPathsDialog.warning() did not accept a callback parameter, causing a
    TypeError that swallowed the error silently.

    Fix: LoadPathsDialog.warning() now accepts an optional callback, and the
    error message names the expected extensions so the user knows how to fix it.
    """
    (tmp_path / "my_named_paths.json").write_text('{"group": ["file.csvpath"]}')
    (tmp_path / "notes.txt").write_text("some text")

    loader, dialog = _make_loader_and_dialog(main, str(tmp_path))
    dialog.named_paths_name_ctl.setText("dir-group")

    warnings_shown = []
    monkeypatch.setattr(
        dialog,
        "warning",
        lambda msg, title, callback=None: warnings_shown.append((msg, title)),
    )

    loader._do_load_dir_answer(
        QMessageBox.Yes,
        paths=main.csvpaths,
        named_paths_name="dir-group",
        name=str(tmp_path),
        template=None,
    )

    assert len(warnings_shown) >= 1, (
        "A warning must be shown when the directory has no valid csvpath files"
    )
    msg, title = warnings_shown[0]
    assert "csvpath" in msg.lower(), (
        f"Warning must mention csvpath extensions; got: {msg!r}"
    )


def test_load_dir_warning_callback_does_not_crash(monkeypatch, tmp_path, main):
    """
    LoadPathsDialog.warning() must accept an optional callback without raising
    TypeError.

    Previously warning(msg, title) rejected a callback keyword argument, which
    crashed _do_load_dir_answer before the user ever saw an error message.
    """
    loader, dialog = _make_loader_and_dialog(main, str(tmp_path))

    callback_called = []
    dialog.warning(
        msg="test message",
        title="Test",
        callback=lambda answer: callback_called.append(answer),
    )
    # No TypeError raised — test passes if we reach this line.


def test_load_json_definition_writes_pretty_printed_definition_json(
    qtbot, tmp_path, main
):
    """
    Loading a JSON definition file must write a pretty-printed definition.json
    (indent=2) inside the named-paths group directory.

    add_named_paths_from_json() calls store_json_paths_file() which delegates
    to paths_describer.store_json(), using json.dump(j, writer.sink, indent=2).
    The resulting file must contain newlines so it remains readable as the
    definition grows with additional paths.
    """
    csvpath_file = _examples(main, "first steps", "Hello World.csvpath")
    json_data = {"json-def-group": [csvpath_file]}
    json_path = tmp_path / "definition.json"
    json_path.write_text(json.dumps(json_data))

    main.csvpaths.paths_manager.add_named_paths_from_json(file_path=str(json_path))

    def_json = os.path.join(
        _named_paths_root(main), "json-def-group", "definition.json"
    )
    assert os.path.isfile(def_json), f"definition.json must exist after JSON load: {def_json}"

    content = open(def_json).read()
    assert "\n" in content, (
        "definition.json must be pretty-printed (contain newlines); "
        f"got: {content!r}"
    )
    parsed = json.loads(content)
    assert "json-def-group" in parsed, (
        "definition.json must contain the loaded group name"
    )


def test_copy_back_of_definition_json_preserves_pretty_printing(qtbot, tmp_path, main):
    """
    Copy-back of a definition.json from the named-paths sidebar must produce
    a pretty-printed file in the project working directory.

    The copy-back flow (JsonViewer2._copy_back_answer → fiut.copy_results_back_to_cwd)
    copies the raw file bytes; the test verifies those bytes contain newlines,
    i.e. that the on-disk definition.json written by the library is already
    pretty-printed and is faithfully reproduced by the copy.
    """
    csvpath_file = _examples(main, "first steps", "Hello World.csvpath")
    json_data = {"copy-back-group": [csvpath_file]}
    json_path = tmp_path / "definition.json"
    json_path.write_text(json.dumps(json_data))

    main.csvpaths.paths_manager.add_named_paths_from_json(file_path=str(json_path))

    source_def = os.path.join(
        _named_paths_root(main), "copy-back-group", "definition.json"
    )
    assert os.path.isfile(source_def), f"source definition.json must exist: {source_def}"

    # Open the definition.json as UNEDITABLE, as the named-paths sidebar does.
    main.read_validate_and_display_file_for_path(source_def, editable=EditStates.UNEDITABLE)
    qtbot.waitUntil(
        lambda: taut.find_tab(main.content.tab_widget, source_def) is not None,
        timeout=TIMEOUT,
    )
    viewer = taut.find_tab(main.content.tab_widget, source_def)[1]
    assert isinstance(viewer, JsonViewer2), (
        "definition.json must open in JsonViewer2"
    )

    # Suppress the subsequent re-open so we can inspect the copied file directly.
    main.read_validate_and_display_file_for_path = lambda *a, **kw: None

    viewer._copy_back_answer(QMessageBox.Yes)

    copied = os.path.join(main.state.cwd, "definition.json")
    assert os.path.isfile(copied), (
        f"copy-back must write definition.json to the project cwd: {copied}"
    )
    content = open(copied).read()
    assert "\n" in content, (
        "Copied definition.json must be pretty-printed (contain newlines); "
        f"got: {content!r}"
    )
    parsed = json.loads(content)
    assert "copy-back-group" in parsed, (
        "Copied definition.json must contain the group name"
    )
