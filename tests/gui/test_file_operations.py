"""
pytest-qt tests for sidebar file operations: rename, copy+paste, cut+paste.

Checklist coverage:
  HOME > file operations > rename file
  HOME > file operations > copy file
  HOME > file operations > cut, copy, paste

Rename uses a synchronous QInputDialog.exec() dialog — same monkeypatch
pattern as the creation tests in test_sidebar_context_menu.py.

Paste destination is controlled via sidebar._last_path (set by the right-click
that opens the context menu) rather than _current_path() (the stale tree
selection, which reflects the last left-click and does not represent user
intent for the paste destination).

  _last_path = None      → paste into cwd  (user right-clicked whitespace)
  _last_path = <dir>     → paste into that directory
  _last_path = <file>    → paste into the file's parent directory

Run with:
  QT_QPA_PLATFORM=offscreen poetry run python -m pytest tests/gui/test_file_operations.py -v
"""

import os

# isolated_home and main fixtures are provided by conftest.py

MODULE = "flightpath.widgets.sidebars.sidebar_actions"


def _make_dialog(name: str, accepted: bool = True):
    """QInputDialog stub — same factory pattern as test_sidebar_context_menu."""
    class _FakeDialog:
        def setFixedSize(self, *a): pass
        def setLabelText(self, *a): pass
        def setTextValue(self, *a): pass
        def exec(self): return 1 if accepted else 0
        def textValue(self): return name
    return _FakeDialog


def _make_file(main, filename, content="a,b\n1,2\n") -> str:
    path = os.path.join(main.state.cwd, filename)
    with open(path, "w") as f:
        f.write(content)
    return path


# ========= TESTS ============


def test_rename_file(monkeypatch, main):
    """
    'Rename' must move the file to the new name in the same directory.
    The old path must no longer exist and the new one must.
    """
    original = _make_file(main, "original.csv")
    new_name = "renamed.csv"
    expected = os.path.join(main.state.cwd, new_name)

    monkeypatch.setattr(MODULE + ".QInputDialog", _make_dialog(new_name))
    monkeypatch.setattr(main.sidebar.actions, "_current_path", lambda: original)

    main.sidebar.actions._rename_file_navigator_item()

    assert not os.path.exists(original), "Original file should be gone after rename"
    assert os.path.isfile(expected), f"Renamed file not found: {expected}"


def test_rename_cancel_keeps_file(monkeypatch, main):
    """
    Cancelling the rename dialog must leave the original file untouched.
    """
    original = _make_file(main, "keep_me.csv")

    monkeypatch.setattr(MODULE + ".QInputDialog", _make_dialog("anything.csv", accepted=False))
    monkeypatch.setattr(main.sidebar.actions, "_current_path", lambda: original)

    main.sidebar.actions._rename_file_navigator_item()

    assert os.path.isfile(original), "File should be unchanged after cancelling rename"


# ---------------------------------------------------------------------------
# Copy + paste
# ---------------------------------------------------------------------------

def test_copy_paste_into_directory_creates_deconflicted_copy(main):
    """
    Copy then paste (right-click on a directory) must leave the original
    intact and create a deconflicted copy in the destination directory.
    _last_path is set to the destination directory, as the context menu does.
    """
    source = _make_file(main, "source.csv")
    dest_dir = main.state.cwd

    main.sidebar.copied = source
    main.sidebar.cutted = None
    main.sidebar._last_path = dest_dir  # user right-clicked the destination dir

    main.sidebar.actions._paste()

    assert os.path.isfile(source), "Original must survive a copy+paste"
    copy_path = os.path.join(dest_dir, "source(0).csv")
    assert os.path.isfile(copy_path), f"Deconflicted copy not found: {copy_path}"
    assert main.sidebar.copied is None, "sidebar.copied must be cleared after paste"


def test_copy_paste_into_whitespace_uses_cwd(main):
    """
    Pasting after right-clicking whitespace (_last_path = None) must copy
    into cwd.  This is the key scenario from the bug report: the user copied
    README.md, right-clicked whitespace to paste, and got a NotADirectoryError
    because _paste was reading _current_path() (stale tree selection pointing
    at xyz.json) instead of _last_path.
    """
    source = _make_file(main, "readme_copy_test.md", content="# hello\n")

    main.sidebar.copied = source
    main.sidebar.cutted = None
    main.sidebar._last_path = None  # user right-clicked whitespace

    main.sidebar.actions._paste()

    assert os.path.isfile(source), "Original must survive copy+paste into whitespace"
    copy_path = os.path.join(main.state.cwd, "readme_copy_test(0).md")
    assert os.path.isfile(copy_path), (
        f"Paste into whitespace must copy to cwd; expected: {copy_path}"
    )


def test_copy_paste_when_last_path_is_file_pastes_to_parent_dir(main):
    """
    When _last_path is a file (user right-clicked a file to open the menu
    that contains Paste), paste must copy into the file's parent directory.

    Previously _paste used _current_path() which could return a stale tree
    selection that treated the file as a directory destination.
    """
    source = _make_file(main, "to_copy.csv")
    sibling = _make_file(main, "sibling.csv")

    main.sidebar.copied = source
    main.sidebar.cutted = None
    main.sidebar._last_path = sibling  # right-clicked a sibling file

    main.sidebar.actions._paste()

    copy_path = os.path.join(main.state.cwd, "to_copy(0).csv")
    assert os.path.isfile(copy_path), (
        f"Paste with a file _last_path must land in the file's parent dir: {copy_path}"
    )
    assert os.path.isfile(source), "Original must be intact after copy+paste"


# ---------------------------------------------------------------------------
# Cut + paste
# ---------------------------------------------------------------------------

#chked
def test_cut_paste_moves_file_to_directory(main):
    """
    Cut then paste (right-click on a directory) must remove the file from its
    original location and place it in the destination directory.
    """
    source = _make_file(main, "to_move.csv")
    dest_dir = os.path.join(main.state.cwd, "subdir")
    os.mkdir(dest_dir)

    main.sidebar.cutted = source
    main.sidebar.copied = None
    main.sidebar._last_path = dest_dir  # user right-clicked the destination dir

    main.sidebar.actions._paste()

    assert not os.path.exists(source), "Original must be gone after cut+paste"
    assert os.path.isfile(os.path.join(dest_dir, "to_move.csv")), (
        "File must appear in destination after cut+paste"
    )
    assert main.sidebar.cutted is None, "sidebar.cutted must be cleared after paste"


def test_cut_paste_when_last_path_is_file_moves_to_parent_dir(main):
    """
    Cut+paste with a file _last_path must move the source into the file's
    parent directory, not attempt to write inside the file itself.
    """
    source = _make_file(main, "to_cut.csv")
    dest_dir = os.path.join(main.state.cwd, "subdir2")
    os.mkdir(dest_dir)
    anchor = os.path.join(dest_dir, "anchor.csv")
    with open(anchor, "w") as f:
        f.write("x\n")

    main.sidebar.cutted = source
    main.sidebar.copied = None
    main.sidebar._last_path = anchor  # right-clicked a file inside subdir2

    main.sidebar.actions._paste()

    assert not os.path.exists(source), "Source must be gone after cut+paste"
    assert os.path.isfile(os.path.join(dest_dir, "to_cut.csv")), (
        "Cut file must land in the file's parent directory"
    )


def test_paste_ignores_stale_tree_selection(monkeypatch, main):
    """
    _paste must use _last_path, not _current_path().  Even when _current_path()
    would return a file (stale tree selection), paste into whitespace
    (_last_path = None) must go to cwd — not into the stale file path.
    """
    source = _make_file(main, "paste_stale_test.csv")
    stale_file = _make_file(main, "stale_selection.json", content="{}")

    main.sidebar.copied = source
    main.sidebar.cutted = None
    main.sidebar._last_path = None  # whitespace right-click

    # Stale tree selection points at a file — _paste must ignore this
    monkeypatch.setattr(main.sidebar.actions, "_current_path", lambda: stale_file)

    main.sidebar.actions._paste()

    copy_path = os.path.join(main.state.cwd, "paste_stale_test(0).csv")
    assert os.path.isfile(copy_path), (
        "Paste must land in cwd when _last_path is None, "
        "regardless of what _current_path() returns"
    )
    bad_path = os.path.join(os.path.dirname(stale_file), "paste_stale_test(0).csv")
    # bad_path == copy_path here since both are in cwd, so check the stale
    # nested path was never attempted
    assert not os.path.exists(os.path.join(stale_file, "paste_stale_test(0).csv")), (
        "Paste must not attempt to write inside the stale file path"
    )
