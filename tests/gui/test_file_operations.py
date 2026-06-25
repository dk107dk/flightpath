"""
pytest-qt tests for sidebar file operations: rename, copy+paste, cut+paste.

Checklist coverage:
  HOME > file operations > rename file
  HOME > file operations > copy file
  HOME > file operations > cut, copy, paste

Rename uses a synchronous QInputDialog.exec() dialog — same monkeypatch
pattern as the creation tests in test_sidebar_context_menu.py.

Copy and cut bypass the _copy()/_cut() action methods and set
sidebar.copied / sidebar.cutted directly (the same state those methods
produce), then drive _paste() with _current_path monkeypatched to the
desired destination directory.  This avoids double-patching _current_path
for source-then-destination in a single test.

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


def test_copy_paste_creates_duplicate(monkeypatch, main):
    """
    Copy then paste must leave the original intact and create a deconflicted
    copy (e.g. 'source(0).csv') in the destination directory.
    """
    source = _make_file(main, "source.csv")
    dest_dir = main.state.cwd

    # Set the copied path directly — equivalent to calling _copy() with source selected
    main.sidebar.copied = source
    main.sidebar.cutted = None

    # Paste into cwd (a directory)
    monkeypatch.setattr(main.sidebar.actions, "_current_path", lambda: dest_dir)
    main.sidebar.actions._paste()

    assert os.path.isfile(source), "Original must survive a copy+paste"
    # FileUtility.deconflicted_path produces 'source(0).csv' when 'source.csv' exists
    copy_path = os.path.join(dest_dir, "source(0).csv")
    assert os.path.isfile(copy_path), f"Deconflicted copy not found: {copy_path}"
    assert main.sidebar.copied is None, "sidebar.copied must be cleared after paste"

#chked
def test_cut_paste_moves_file(monkeypatch, main):
    """
    Cut then paste must remove the file from its original location and
    place it in the destination directory under the same name.
    """
    source = _make_file(main, "to_move.csv")
    dest_dir = os.path.join(main.state.cwd, "subdir")
    os.mkdir(dest_dir)

    # Set the cutted path directly — equivalent to calling _cut() with source selected
    main.sidebar.cutted = source
    main.sidebar.copied = None

    monkeypatch.setattr(main.sidebar.actions, "_current_path", lambda: dest_dir)
    main.sidebar.actions._paste()

    assert not os.path.exists(source), "Original must be gone after cut+paste"
    assert os.path.isfile(os.path.join(dest_dir, "to_move.csv")), (
        "File must appear in destination after cut+paste"
    )
    assert main.sidebar.cutted is None, "sidebar.cutted must be cleared after paste"


def test_copy_paste_when_current_path_is_file_pastes_to_parent_dir(monkeypatch, main):
    """
    When the selected item is a file (not a directory), paste must copy into
    the file's parent directory — not treat the file itself as the destination.

    This was the root cause of the NotADirectoryError traceback:
      shutil.copy(src, '/path/to/tsetsl.json/README.md')
    because _paste used _current_path() directly as the destination dir.
    """
    source = _make_file(main, "to_copy.csv")
    sibling = _make_file(main, "sibling.csv")   # a file in the same dir

    main.sidebar.copied = source
    main.sidebar.cutted = None

    # Simulate the user right-clicking on a file (sibling) rather than whitespace
    monkeypatch.setattr(main.sidebar.actions, "_current_path", lambda: sibling)
    main.sidebar.actions._paste()

    # Should land in cwd (parent of sibling), not inside sibling
    copy_path = os.path.join(main.state.cwd, "to_copy(0).csv")
    assert os.path.isfile(copy_path), (
        f"Copy+paste with a file as current path must paste into that file's "
        f"parent directory; expected: {copy_path}"
    )
    assert os.path.isfile(source), "Original must be intact after copy+paste"


def test_cut_paste_when_current_path_is_file_moves_to_parent_dir(monkeypatch, main):
    """
    Cut+paste must also use the parent directory when the selected item is a
    file, not the file path itself as the destination.
    """
    source = _make_file(main, "to_cut.csv")
    dest_dir = os.path.join(main.state.cwd, "subdir2")
    os.mkdir(dest_dir)
    sibling_in_subdir = os.path.join(dest_dir, "anchor.csv")
    with open(sibling_in_subdir, "w") as f:
        f.write("x\n")

    main.sidebar.cutted = source
    main.sidebar.copied = None

    # Simulate selecting a file inside subdir2 rather than the directory itself
    monkeypatch.setattr(main.sidebar.actions, "_current_path", lambda: sibling_in_subdir)
    main.sidebar.actions._paste()

    assert not os.path.exists(source), "Source must be gone after cut+paste"
    assert os.path.isfile(os.path.join(dest_dir, "to_cut.csv")), (
        "Cut file must move to the selected file's parent directory"
    )



