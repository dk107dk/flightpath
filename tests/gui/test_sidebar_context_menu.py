"""
pytest-qt tests for sidebar context-menu file/folder creation, deletion, and
path resolution.

_resolve_new_item_path coverage
--------------------------------
Bug fixed: line 398 of sidebar_actions.py read self._last_path instead of
self.my_parent._last_path.  When _last_path was set on Sidebar, the method
raised AttributeError because SidebarActions has no such attribute.

Three branches:
  1. name already starts with cwd → returned unchanged (absolute path passed in)
  2. _last_path is None → os.path.join(cwd, name)  (no prior selection)
  3. _last_path is set → os.path.join(cwd, _last_path, name)  (relative to last
     selected directory — this was the broken branch)

pytest-qt tests for sidebar context-menu file/folder creation and deletion.

Checklist coverage:
  HOME > create files > create CSV file
  HOME > create files > create csvpath file
  HOME > create files > create md file
  HOME > create files > create json file
  HOME > create files > create JSONL file
  HOME > create directory
  HOME > file operations > delete file
  HOME > file operations > delete directory
  HOME > permanent delete (named-files, named-paths, archive)

Creation tests
--------------
The 'New file' and 'New folder' actions use synchronous QInputDialog.exec()
dialogs.  Tests monkeypatch the QInputDialog class in the sidebar_actions
module so the dialog is never shown; the stub immediately returns the
test-supplied filename/folder name.

Deletion tests
--------------
The 'Delete' action calls meut.yesNo2 (non-blocking QMessageBox) and, on
confirmation, delegates to _do_delete_item.  Tests patch:
  • sidebar.actions._current_path — to return a pre-created test file path
    without needing the QFileSystemModel to populate first.
  • MessageUtility.yesNo2 — replaced with a synchronous stub that immediately
    fires the callback with Yes or No, eliminating dialog timing issues.

Each test:
  1. Patches the relevant inputs in the module where they are imported.
  2. Calls the action method directly (bypassing the right-click event).
  3. Asserts the expected filesystem outcome.
  3. Asserts that the expected file/directory exists on disk and, for text
     files, that the starter content is correct.

Run with:
  QT_QPA_PLATFORM=offscreen poetry run python -m pytest tests/gui/test_sidebar_context_menu.py -v
"""

import os

from PySide6.QtCore import QPoint
from PySide6.QtWidgets import QMessageBox

from flightpath.util.message_utility import MessageUtility

# isolated_home and main fixtures are provided by conftest.py

MODULE = "flightpath.widgets.sidebars.sidebar_actions"


def _make_dialog(name: str, accepted: bool = True, get_item_result: str = "{}"):
    """Return a QInputDialog stub that reports *name* and *accepted*.

    *get_item_result* is returned by the getItem() static method used when
    the action prompts for a JSON data-structure choice.
    """
    _result = get_item_result

    class _FakeDialog:
        def setFixedSize(self, *a):
            pass

        def setLabelText(self, *a):
            pass

        def exec(self):
            return 1 if accepted else 0

        def textValue(self):
            return name

        @staticmethod
        def getItem(*a, **kw):
            return _result, True

    return _FakeDialog


# ========= TESTS ============

#chked
def test_new_csv_file_creates_file(monkeypatch, main):
    """
    'New file' → 'new_data.csv' must create the file under the project root
    and write a single comma as starter content.
    """
    filename = "new_data.csv"
    monkeypatch.setattr(MODULE + ".QInputDialog", _make_dialog(filename))

    main.sidebar._last_path = None
    main.sidebar.actions._new_file_navigator_item()

    expected = os.path.join(main.state.cwd, filename)
    assert os.path.isfile(expected), f"Expected file not created: {expected}"
    assert open(expected).read() == ","

#chked
def test_new_md_file_creates_file(monkeypatch, main):
    """
    'New file' → 'notes.md' must create the file with the Markdown starter
    template that begins with '# Title'.
    """
    filename = "notes.md"
    monkeypatch.setattr(MODULE + ".QInputDialog", _make_dialog(filename))

    main.sidebar._last_path = None
    main.sidebar.actions._new_file_navigator_item()

    expected = os.path.join(main.state.cwd, filename)
    assert os.path.isfile(expected), f"Expected file not created: {expected}"
    assert open(expected).read().startswith("# Title")

#chked
def test_new_csvpath_file_creates_file(monkeypatch, main):
    """
    'New file' → 'check.csvpath' must create the file with the csvpath
    starter template that contains the 'hello world' id.
    """
    filename = "check.csvpath"
    monkeypatch.setattr(MODULE + ".QInputDialog", _make_dialog(filename))

    main.sidebar._last_path = None
    main.sidebar.actions._new_file_navigator_item()

    expected = os.path.join(main.state.cwd, filename)
    assert os.path.isfile(expected), f"Expected file not created: {expected}"
    assert "hello world" in open(expected).read()

#chked
def test_new_json_file_creates_file(monkeypatch, main):
    """
    'New file' → 'data.json' must create the file.  JSON files prompt for
    the initial data structure ({} or []); the stub selects '{}'.
    """
    filename = "data.json"
    # _make_dialog includes a getItem() stub returning "{}" for JSON files
    monkeypatch.setattr(MODULE + ".QInputDialog", _make_dialog(filename, get_item_result="{}"))

    main.sidebar._last_path = None
    main.sidebar.actions._new_file_navigator_item()

    expected = os.path.join(main.state.cwd, filename)
    assert os.path.isfile(expected), f"Expected file not created: {expected}"
    assert open(expected).read() == "{}"

#chked
def test_new_jsonl_file_creates_file_with_object(monkeypatch, main):
    """
    'New file' → 'events.jsonl' must create the file.  JSONL files share the
    JSON creation path and prompt for an initial data structure via getItem();
    the stub selects '{}', so the file content must be '{}'.
    """
    filename = "events.jsonl"
    monkeypatch.setattr(MODULE + ".QInputDialog", _make_dialog(filename, get_item_result="{}"))

    main.sidebar._last_path = None
    main.sidebar.actions._new_file_navigator_item()

    expected = os.path.join(main.state.cwd, filename)
    assert os.path.isfile(expected), f"Expected JSONL file not created: {expected}"
    assert open(expected).read() == "{}"

#chked
def test_new_jsonl_file_creates_file_with_array(monkeypatch, main):
    """
    'New file' → 'items.jsonl' with getItem() returning '[]' must create the
    file with '[]' as starter content (array variant of the JSONL creation flow).
    """
    filename = "items.jsonl"
    monkeypatch.setattr(MODULE + ".QInputDialog", _make_dialog(filename, get_item_result="[]"))

    main.sidebar._last_path = None
    main.sidebar.actions._new_file_navigator_item()

    expected = os.path.join(main.state.cwd, filename)
    assert os.path.isfile(expected), f"Expected JSONL file not created: {expected}"
    assert open(expected).read() == "[]"

def test_new_folder_creates_directory(monkeypatch, main):
    """
    'New folder' → 'my_data' must create the directory under the project root.
    """
    folder = "my_data"
    monkeypatch.setattr(MODULE + ".QInputDialog", _make_dialog(folder))

    main.sidebar._last_path = None
    main.sidebar.actions._new_folder_navigator_item()

    expected = os.path.join(main.state.cwd, folder)
    assert os.path.isdir(expected), f"Expected directory not created: {expected}"


# ---------------------------------------------------------------------------
# Deconfliction tests — duplicate filename on New File
# ---------------------------------------------------------------------------

def test_new_file_duplicate_name_creates_deconflicted_copy(monkeypatch, main):
    """
    Creating a file whose name already exists must produce a deconflicted name
    (e.g. test(0).csv) rather than silently overwriting the original.

    Previously open(..., 'w') overwrote the existing file with starter content
    and gave no feedback.  Now fiut.deconflicted_path is applied before writing.
    """
    filename = "dup_test.csv"
    original = os.path.join(main.state.cwd, filename)
    with open(original, "w") as f:
        f.write("original,content\n")

    monkeypatch.setattr(MODULE + ".QInputDialog", _make_dialog(filename))
    main.sidebar._last_path = None
    main.sidebar.actions._new_file_navigator_item()

    deconflicted = os.path.join(main.state.cwd, "dup_test(0).csv")
    assert os.path.isfile(deconflicted), (
        f"Duplicate filename must create a deconflicted file: {deconflicted}"
    )
    with open(original) as f:
        assert f.read() == "original,content\n", (
            "Original file must be untouched when a deconflicted copy is created"
        )


def test_new_file_unique_name_creates_without_suffix(monkeypatch, main):
    """
    Creating a file whose name does not already exist must use exactly the
    entered name — no deconfliction suffix should be added.
    """
    filename = "unique_file.csv"
    monkeypatch.setattr(MODULE + ".QInputDialog", _make_dialog(filename))
    main.sidebar._last_path = None
    main.sidebar.actions._new_file_navigator_item()

    expected = os.path.join(main.state.cwd, filename)
    assert os.path.isfile(expected), f"Unique filename must be used as-is: {expected}"
    suffixed = os.path.join(main.state.cwd, "unique_file(0).csv")
    assert not os.path.exists(suffixed), (
        "No deconfliction suffix must be added for a name that does not already exist"
    )


def test_new_file_duplicate_shows_status_bar_with_actual_name(monkeypatch, main):
    """
    After a deconflicted create, the status bar must show the actual filename
    used so the user knows what was created.
    """
    filename = "status_dup.csv"
    original = os.path.join(main.state.cwd, filename)
    with open(original, "w") as f:
        f.write("x\n")

    monkeypatch.setattr(MODULE + ".QInputDialog", _make_dialog(filename))
    main.sidebar._last_path = None
    main.sidebar.actions._new_file_navigator_item()

    msg = main.statusBar().currentMessage()
    assert "status_dup(0).csv" in msg, (
        f"Status bar must mention the deconflicted filename; got: '{msg}'"
    )


# ---------------------------------------------------------------------------
# Helpers for deletion tests
# ---------------------------------------------------------------------------

def _make_test_file(main, filename="to_delete.csv") -> str:
    """Create a real file in the project root and return its absolute path."""
    path = os.path.join(main.state.cwd, filename)
    with open(path, "w") as f:
        f.write("a,b\n1,2\n")
    return path


def _patch_yes_no2(monkeypatch, answer: int) -> None:
    """
    Replace MessageUtility.yesNo2 with a synchronous stub that immediately
    calls the callback with *answer* (QMessageBox.Yes or QMessageBox.No).
    """
    def _fake(*, parent, callback, msg, title="", args=None):
        callback(answer, **(args or {}))

    monkeypatch.setattr(MessageUtility, "yesNo2", _fake)


# ---------------------------------------------------------------------------
# Deletion tests
# ---------------------------------------------------------------------------

#chked
def test_delete_file_yes_removes_file(monkeypatch, main):
    """
    Confirming 'Delete' (Yes) must remove the file from disk.
    The full action path is exercised: _delete_file_navigator_item →
    yesNo2 (stubbed) → _do_delete_item → Nos.remove().
    """
    path = _make_test_file(main)
    assert os.path.isfile(path)

    _patch_yes_no2(monkeypatch, QMessageBox.Yes)
    monkeypatch.setattr(main.sidebar.actions, "_current_path", lambda: path)

    main.sidebar.actions._delete_file_navigator_item()

    assert not os.path.exists(path), "File should be deleted after confirming Yes"

#chked
def test_delete_file_no_keeps_file(monkeypatch, main):
    """
    Cancelling 'Delete' (No) must leave the file untouched on disk.
    """
    path = _make_test_file(main)
    assert os.path.isfile(path)

    _patch_yes_no2(monkeypatch, QMessageBox.No)
    monkeypatch.setattr(main.sidebar.actions, "_current_path", lambda: path)

    main.sidebar.actions._delete_file_navigator_item()

    assert os.path.isfile(path), "File should still exist after cancelling (No)"

#chked
def test_delete_selected_file_shows_welcome(monkeypatch, main):
    """
    Deleting the currently-open file (is_selected=True) must call
    show_welcome_screen() so the content pane doesn't display a stale viewer.
    """
    path = _make_test_file(main)
    main.selected_file_path = path  # mark as the open file

    welcome_calls = []
    monkeypatch.setattr(main, "show_welcome_screen", lambda: welcome_calls.append(1))

    _patch_yes_no2(monkeypatch, QMessageBox.Yes)
    monkeypatch.setattr(main.sidebar.actions, "_current_path", lambda: path)

    main.sidebar.actions._delete_file_navigator_item()

    assert not os.path.exists(path)
    assert len(welcome_calls) == 1, "show_welcome_screen() must be called for the selected file"

#chked
def test_delete_directory_yes_removes_dir(monkeypatch, main):
    """
    Confirming 'Delete' (Yes) on a directory path must remove the entire
    directory from disk.  Nos.remove() handles both files and directories, so
    the same _delete_file_navigator_item action covers both cases.
    """
    dir_path = os.path.join(main.state.cwd, "dir_to_delete")
    os.mkdir(dir_path)
    assert os.path.isdir(dir_path)

    _patch_yes_no2(monkeypatch, QMessageBox.Yes)
    monkeypatch.setattr(main.sidebar.actions, "_current_path", lambda: dir_path)

    main.sidebar.actions._delete_file_navigator_item()

    assert not os.path.exists(dir_path), "Directory should be removed after confirming Yes"

#chked
def test_delete_directory_no_keeps_dir(monkeypatch, main):
    """
    Cancelling 'Delete' (No) on a directory must leave it untouched on disk.
    """
    dir_path = os.path.join(main.state.cwd, "keep_this_dir")
    os.mkdir(dir_path)
    assert os.path.isdir(dir_path)

    _patch_yes_no2(monkeypatch, QMessageBox.No)
    monkeypatch.setattr(main.sidebar.actions, "_current_path", lambda: dir_path)

    main.sidebar.actions._delete_file_navigator_item()

    assert os.path.isdir(dir_path), "Directory should survive after cancelling (No)"


# ---------------------------------------------------------------------------
# _resolve_new_item_path — unit tests
# ---------------------------------------------------------------------------

def test_resolve_absolute_path_returned_unchanged(main):
    """
    When the name already starts with cwd (i.e. is an absolute path), it must
    be returned as-is — no join is applied.
    """
    cwd = main.state.cwd
    absolute = os.path.join(cwd, "subdir", "file.csv")
    result = main.sidebar.actions._resolve_new_item_path(absolute)
    assert result == absolute


def test_resolve_no_last_path_joins_cwd_and_name(main):
    """
    When _last_path is None (no prior tree selection), the path must be
    os.path.join(cwd, name) — placed at the project root.
    """
    main.sidebar._last_path = None
    result = main.sidebar.actions._resolve_new_item_path("new_file.csv")
    assert result == os.path.join(main.state.cwd, "new_file.csv")


def test_resolve_with_last_path_joins_cwd_last_path_and_name(main):
    """
    When _last_path is set on Sidebar to a directory, the resolved path must be
    os.path.join(_last_path, name) — _last_path is always an absolute path set
    by the context menu, so cwd is not prepended.
    """
    examples_dir = os.path.join(main.state.cwd, "examples")
    main.sidebar._last_path = examples_dir
    result = main.sidebar.actions._resolve_new_item_path("check.csvpath")
    assert result == os.path.join(examples_dir, "check.csvpath")
    main.sidebar._last_path = None  # restore so other tests aren't affected


def test_resolve_with_last_path_as_file_uses_parent_directory(main):
    """
    When _last_path points to a file (the user right-clicked a file before
    choosing New File), the resolved path must land in the file's parent
    directory, not try to nest inside the file itself.

    Previously os.path.join(cwd, last_path, name) treated the file as a
    directory, producing '/path/to/file.json/new.csv' which fails at open().
    """
    existing = os.path.join(main.state.cwd, "anchor.json")
    with open(existing, "w") as f:
        f.write("{}")

    main.sidebar._last_path = existing   # absolute path to a file
    result = main.sidebar.actions._resolve_new_item_path("new_file.csv")
    assert result == os.path.join(main.state.cwd, "new_file.csv"), (
        "When _last_path is a file, new item must be created in its parent directory"
    )
    main.sidebar._last_path = None


def test_show_context_menu_syncs_current_index_to_right_clicked_item(monkeypatch, main):
    """
    _show_context_menu() must call file_navigator.setCurrentIndex() with the
    item at the right-click position so that _current_path() (which reads
    currentIndex()) returns the right-clicked item rather than the previously
    left-clicked selection.

    Bug: right-clicking definition.json while a parent directory was selected
    showed the correct context menu (the menu uses indexAt(position)), but
    the triggered 'Load csvpaths' action called _current_path() which returned
    the stale directory.  This caused do_load_dir() to run instead of
    do_load_json(), and the library raised ValueError: Must end in :run_dir.

    Fix: _show_context_menu() now calls file_navigator.setCurrentIndex(index)
    before building the menu, syncing the selection to the right-clicked item.
    """
    from unittest.mock import MagicMock
    from PySide6.QtCore import QModelIndex

    nav = main.sidebar.file_navigator

    fake_index = MagicMock(spec=QModelIndex)
    fake_index.isValid.return_value = True

    monkeypatch.setattr(nav, "indexAt", lambda pos: fake_index)

    set_calls = []
    monkeypatch.setattr(nav, "setCurrentIndex", lambda idx: set_calls.append(idx))
    monkeypatch.setattr(
        main.sidebar.context_menu_maker,
        "show_context_menu",
        lambda pos: None,
    )

    main.sidebar._show_context_menu(QPoint(5, 5))

    assert len(set_calls) == 1, (
        "_show_context_menu() must call setCurrentIndex() exactly once"
    )
    assert set_calls[0] is fake_index, (
        "_show_context_menu() must call setCurrentIndex() with the indexAt() result, "
        "not the stale currentIndex()"
    )


def test_show_context_menu_does_not_change_index_for_invalid_position(monkeypatch, main):
    """
    When the right-click position maps to no tree item (e.g. whitespace below
    the last row), _show_context_menu() must NOT call setCurrentIndex() so the
    existing selection is not cleared.
    """
    from unittest.mock import MagicMock
    from PySide6.QtCore import QModelIndex

    nav = main.sidebar.file_navigator

    invalid_index = MagicMock(spec=QModelIndex)
    invalid_index.isValid.return_value = False
    monkeypatch.setattr(nav, "indexAt", lambda pos: invalid_index)

    set_calls = []
    monkeypatch.setattr(nav, "setCurrentIndex", lambda idx: set_calls.append(idx))
    monkeypatch.setattr(
        main.sidebar.context_menu_maker,
        "show_context_menu",
        lambda pos: None,
    )

    main.sidebar._show_context_menu(QPoint(999, 999))

    assert len(set_calls) == 0, (
        "_show_context_menu() must not call setCurrentIndex() when the position "
        "maps to no valid tree item"
    )
