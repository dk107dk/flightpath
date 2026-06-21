"""
First pytest-qt test for FlightPath: the "create new project" workflow.

Covers:
  1. The projects combo box contains Sidebar.NEW_PROJECT.
  2. Selecting it opens the new-project dialog, which takes a name and submits.
  3. State.current_project switches to the new name and MainWindow re-lays-out
     (startup() runs again) against the new cwd.
  4. The new project directory has an examples/ dir populated per
     assets/examples/list.txt.

ASSUMPTIONS — confirm or fix before trusting this test:
  A1. main.state is a State instance and main.sidebar is the Sidebar instance,
      both reachable as plain attributes on the MainWindow.
  A2. MainWindow() can be constructed with no required args beyond what
      pytest-qt/QApplication already provides (i.e. no extra CLI bootstrap
      needed). If MainWindow takes constructor args in your app's normal
      startup path, the `main` fixture below needs those added.
  A3. flightpath/flightpath/assets/examples/list.txt is readable from the
      installed package location at test time (no special packaging step
      needed in dev/test mode).

NOTE on validation: Sidebar.new_project_name -> handle_answer runs the new
name through strut.good_name() and a "does this project already exist" check
before calling back. If either fails, a *second* dialog (meut.warning2, which
is itself a QMessageBox-style dialog, not a QInputDialog) opens and re-asks.
NEW_PROJECT_NAME below is chosen to be safely alphanumeric to avoid tripping
good_name(), and tests assert no QMessageBox-type warning appears, so a
validation failure shows up as a clear assertion instead of a hang waiting on
a dialog.finished that already fired.

Run with:
  QT_QPA_PLATFORM=offscreen poetry run python -m pytest tests/gui/test_new_project_workflow.py -v
"""

import os
from PySide6.QtWidgets import QInputDialog, QMessageBox

from flightpath.widgets.sidebars.sidebar import Sidebar

# isolated_home and main fixtures are provided by conftest.py

EXAMPLES_LIST_PATH = os.path.join(
    os.path.dirname(__file__),
    "..",
    "..",
    "flightpath",
    "assets",
    "examples",
    "list.txt",
)


def _expected_example_entries() -> list[str]:
    with open(EXAMPLES_LIST_PATH, encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]


def _find_open_input_dialog(main) -> QInputDialog | None:
    """
    MessageUtility.input2 parents the QInputDialog on the widget passed as
    `parent`. We search MainWindow's children for any visible QInputDialog.
    """
    for child in main.findChildren(QInputDialog):
        if child.isVisible():
            return child
    return None


def _find_open_warning_dialog(main) -> QMessageBox | None:
    """
    meut.warning2 fires on a failed good_name() or name collision.
    If name is invalid this appears after we accept the QInputDialog.
    """
    for child in main.findChildren(QMessageBox):
        if child.isVisible():
            return child
    return None


# ========= TESTS ============


def test_new_project_combo_has_entry(main):
    c = main.sidebar.projects
    assert c.itemText(c.count() - 1) == Sidebar.NEW_PROJECT


def test_new_project_create_end_to_end(qtbot, main):
    sidebar = main.sidebar
    combo = sidebar.projects

    old_project = main.state.current_project
    assert old_project == "Default"
    old_cwd = main.state.cwd

    # --- Step 1: select "Create new project" -----------------
    index = combo.findText(Sidebar.NEW_PROJECT)
    assert index >= 0, "NEW_PROJECT entry missing from combo"

    with qtbot.waitSignal(combo.currentIndexChanged, timeout=2000):
        combo.setCurrentIndex(index)

    # --- Step 2: the real QInputDialog open --------------------
    # Sidebar.new_project_name -> meut.input2 builds a QInputDialog and calls
    # .open(), which is non-blocking, we can find the child and drive it directly.
    qtbot.waitUntil(lambda: _find_open_input_dialog(main) is not None, timeout=2000)
    dialog = _find_open_input_dialog(main)
    assert dialog is not None, "Expected a QInputDialog to open"

    # --- Step 3: type the project name and submit -----------------------------
    new_name = "Test_Project XYZ-123"
    dialog.setTextValue(new_name)
    with qtbot.waitSignal(dialog.finished, timeout=2000):
        dialog.accept()

    # --- Step 3b: make sure validation didn't reject our chosen name ----------
    # If good_name() or the duplicate check failed, handle_answer opens a
    # warning2 dialog instead of calling back with the name. Fail fast and
    # clearly here rather than timing out later wondering why nothing changed.
    warning = _find_open_warning_dialog(main)
    assert warning is None, (
        f"'{new_name}' was rejected by validation: {warning.text() if warning else ''}"
    )

    # --- Step 4: project should have switched ----------------------------------
    qtbot.waitUntil(lambda: main.state.current_project == new_name, timeout=3000)
    assert main.state.current_project == new_name
    assert main.state.current_project != old_project
    assert main.state.cwd != old_cwd

    new_cwd = main.state.cwd
    assert os.path.isdir(new_cwd), "New project directory was not created"

    # combo should reflect the switch after startup() rebuilds the sidebar
    qtbot.waitUntil(
        lambda: main.sidebar.projects.currentText() == new_name, timeout=2000
    )

    # --- Step 5: config.ini exists (new_project branch ran) --------------------
    config_path = os.path.join(new_cwd, "config", "config.ini")
    assert os.path.exists(config_path)

    # --- Step 6: examples dir populated per list.txt ----------------------------
    examples_dir = os.path.join(new_cwd, "examples")
    assert os.path.isdir(examples_dir)

    expected_entries = _expected_example_entries()
    actual_entries = set(os.listdir(examples_dir))
    for entry in expected_entries:
        # entries in list.txt may be paths like "foo/bar.csv"; only check the
        # top-level piece against the examples dir listing
        top_level = entry.split(os.sep)[0].split("/")[0]
        assert top_level in actual_entries, (
            f"Expected example entry '{top_level}' missing from {examples_dir}"
        )

    # --- Step 7: README.md was created ------------------------------------------
    assert os.path.exists(os.path.join(new_cwd, "README.md"))


def test_new_project_cancel_keeps_current_project(qtbot, main):
    #
    # _make_new_project(None) called on cancel. combo should reset back to current project
    #
    sidebar = main.sidebar
    combo = sidebar.projects
    old_project = main.state.current_project

    index = combo.findText(Sidebar.NEW_PROJECT)
    with qtbot.waitSignal(combo.currentIndexChanged, timeout=2000):
        combo.setCurrentIndex(index)

    qtbot.waitUntil(lambda: _find_open_input_dialog(main) is not None, timeout=2000)
    dialog = _find_open_input_dialog(main)
    assert dialog is not None

    with qtbot.waitSignal(dialog.finished, timeout=2000):
        dialog.reject()

    qtbot.waitUntil(lambda: combo.currentText() == old_project, timeout=2000)
    assert main.state.current_project == old_project
