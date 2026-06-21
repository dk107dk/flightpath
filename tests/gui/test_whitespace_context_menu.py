"""
pytest-qt tests for the left-sidebar whitespace (empty-space) context menu.

Checklist coverage:
  HOME > file operations > right-click on whitespace in project tree

When the user right-clicks on empty space below the last tree item (i.e.
on the viewport but not on any item), QFileSystemModel.indexAt() returns an
invalid QModelIndex.  SidebarContextMenuMaker._build_menu_for() detects this
and calls _build_empty_space_menu() instead of the per-item builders.

The empty-space menu is a root-level menu for project-wide actions:
  • New file / New folder    — add items anywhere in the project
  • Open project directory  — reveal the project folder in Finder/Explorer
  • Paste                   — enabled only when something is cut or copied

File-specific actions (Delete, Rename, Save file, Cut, Copy) must be ABSENT
so the user cannot accidentally operate on a phantom selection.

Tests call _build_menu_for(QModelIndex()) directly to get the menu without
triggering menu.exec() (which would block the test thread).  The returned
QMenu's action texts are used for all assertions.

Run with:
  QT_QPA_PLATFORM=offscreen poetry run python -m pytest tests/gui/test_whitespace_context_menu.py -v
"""

from PySide6.QtCore import QModelIndex

# isolated_home and main fixtures are provided by conftest.py


def _action_texts(main) -> list[str]:
    """Build and return the texts of all actions in the empty-space menu."""
    menu = main.sidebar.context_menu_maker._build_menu_for(QModelIndex())
    return [a.text() for a in menu.actions() if a.text()]


# ---------------------------------------------------------------------------
# Tests — required actions are present
# ---------------------------------------------------------------------------


def test_whitespace_menu_has_new_file_action(main):
    """
    Right-clicking on blank space must offer 'New file' — the primary way to
    add a file to the project without having a directory selected first.
    """
    assert "New file" in _action_texts(main), (
        "Empty-space context menu must contain a 'New file' action"
    )


def test_whitespace_menu_has_new_folder_action(main):
    """
    Right-clicking on blank space must offer 'New folder' for project
    organisation at the root level.
    """
    assert "New folder" in _action_texts(main), (
        "Empty-space context menu must contain a 'New folder' action"
    )


def test_whitespace_menu_has_open_project_dir_action(main):
    """
    Right-clicking on blank space must offer 'Open project directory' — this
    reveals the project folder in Finder/Explorer and is always relevant
    regardless of which item (if any) is selected.
    """
    assert "Open project directory" in _action_texts(main), (
        "Empty-space context menu must contain an 'Open project directory' action"
    )


def test_whitespace_menu_has_paste_action(main):
    """
    Right-clicking on blank space must offer 'Paste' so the user can paste a
    previously cut or copied file into the project root.
    """
    assert "Paste" in _action_texts(main), (
        "Empty-space context menu must contain a 'Paste' action"
    )


def test_whitespace_menu_paste_disabled_when_clipboard_empty(main):
    """
    'Paste' must be disabled when nothing has been cut or copied yet.

    _build_empty_space_menu() checks:
      paste_action.setEnabled(bool(self.my_parent.cutted or self.my_parent.copied))
    On a fresh project neither flag is set, so Paste is disabled.
    """
    menu = main.sidebar.context_menu_maker._build_menu_for(QModelIndex())
    paste = next(a for a in menu.actions() if a.text() == "Paste")
    assert not paste.isEnabled(), (
        "Paste must be disabled in the empty-space menu when nothing is cut or copied"
    )


# ---------------------------------------------------------------------------
# Tests — file-specific actions are absent
# ---------------------------------------------------------------------------


def test_whitespace_menu_excludes_delete_action(main):
    """
    'Delete' must not appear in the empty-space menu — there is no item
    selected, so offering Delete would be misleading or dangerous.
    """
    assert "Delete" not in _action_texts(main), (
        "Empty-space context menu must NOT contain a 'Delete' action"
    )


def test_whitespace_menu_excludes_rename_action(main):
    """
    'Rename' must not appear in the empty-space menu — rename is only
    meaningful on a specific file or directory.
    """
    assert "Rename" not in _action_texts(main), (
        "Empty-space context menu must NOT contain a 'Rename' action"
    )


def test_whitespace_menu_excludes_save_file_action(main):
    """
    'Save file' must not appear in the empty-space menu — saving is only
    meaningful when a specific file is targeted.
    """
    assert "Save file" not in _action_texts(main), (
        "Empty-space context menu must NOT contain a 'Save file' action"
    )
