"""
pytest-qt tests for the Refresh action on the three right-column sidebars.

Checklist coverage:
  HOME > right-column context menu > Refresh (named-files)
  HOME > right-column context menu > Refresh (named-paths)
  HOME > right-column context menu > Refresh (archive)

The three right-panel sidebars (SidebarNamedFiles, SidebarNamedPaths,
SidebarArchive) each have a "Refresh" QAction in their context menus.  The
action calls sidebar.refresh(), which tears down the existing tree view and
calls setup() to rebuild it from the current state of the backend
(local filesystem, S3, Azure Blob, SFTP, etc.).

Two observable outcomes of refresh():
  1. sidebar.view is replaced — the old LazyTreeView is deleted and a fresh
     one is created; the new object is != the old object.
  2. Newly added entries are visible — content added to the backend after the
     sidebar was first built appears in the model after refresh().

Tests:
  • context menu contains a "Refresh" action for all three sidebars
  • refresh() replaces sidebar.view for all three sidebars
  • named-files sidebar picks up a new entry added after initial setup
  • named-paths sidebar picks up a new entry added after initial setup

Note: the archive refresh test only checks view replacement (no archive
content without a production run).

Run with:
  QT_QPA_PLATFORM=offscreen poetry run python -m pytest tests/gui/test_right_sidebar_refresh.py -v
"""

import os

from PySide6.QtCore import QModelIndex

# isolated_home and main fixtures are provided by conftest.py


# ---------------------------------------------------------------------------
# Helpers shared with test_permanent_delete.py
# ---------------------------------------------------------------------------


def _examples(main, *parts) -> str:
    return os.path.join(main.state.cwd, "examples", *parts)


def _inputs_files_root(main) -> str:
    return main.csvpath_config.get(section="inputs", name="files")


def _inputs_csvpaths_root(main) -> str:
    return main.csvpath_config.get(section="inputs", name="csvpaths")


def _register_named_file(main, name: str = "test_refresh") -> str:
    """Register test.csv as a named-file and return its on-disk directory path."""
    csv_file = _examples(main, "first steps", "test.csv")
    csvpaths = main.csvpaths
    csvpaths.config.set(section="inputs", name="allow_local_files", value=True)
    csvpaths.file_manager.add_named_file(name=name, path=csv_file, template=None)
    return os.path.join(_inputs_files_root(main), name)


def _register_named_paths(main, name: str = "test_refresh") -> str:
    """Register Hello World.csvpath as a named-paths group; return on-disk dir."""
    csvpath_file = _examples(main, "first steps", "Hello World.csvpath")
    csvpaths = main.csvpaths
    csvpaths.config.set(section="inputs", name="allow_local_files", value=True)
    csvpaths.paths_manager.add_named_paths_from_file(
        name=name, file_path=csvpath_file, template=None, append=False
    )
    return os.path.join(_inputs_csvpaths_root(main), name)


def _context_menu_action_texts(sidebar) -> list[str]:
    return [a.text() for a in sidebar.context_menu.actions()]


# ---------------------------------------------------------------------------
# Tests — Refresh action present in each context menu
# ---------------------------------------------------------------------------


def test_named_files_context_menu_has_refresh_action(main):
    """
    SidebarNamedFiles must have a 'Refresh' action in its context menu,
    wired to sidebar.refresh().  This is the only way to reload the view
    when data files are open (Welcome and config-form buttons are hidden).
    """
    sidebar = main.sidebar_rt_top
    assert "Refresh" in _context_menu_action_texts(sidebar), (
        "Named-files sidebar context menu must contain a 'Refresh' action"
    )
    assert sidebar.refresh_action.text() == "Refresh"


def test_named_paths_context_menu_has_refresh_action(main):
    """
    SidebarNamedPaths must have a 'Refresh' action in its context menu.
    """
    sidebar = main.sidebar_rt_mid
    assert "Refresh" in _context_menu_action_texts(sidebar), (
        "Named-paths sidebar context menu must contain a 'Refresh' action"
    )
    assert sidebar.refresh_action.text() == "Refresh"


def test_archive_context_menu_has_refresh_action(main):
    """
    SidebarArchive must have a 'Refresh' action in its context menu.
    """
    sidebar = main.sidebar_rt_bottom
    assert "Refresh" in _context_menu_action_texts(sidebar), (
        "Archive sidebar context menu must contain a 'Refresh' action"
    )
    assert sidebar.refresh_action.text() == "Refresh"


# ---------------------------------------------------------------------------
# Tests — refresh() replaces the view
# ---------------------------------------------------------------------------


def test_named_files_refresh_replaces_view(main):
    """
    Calling refresh() on SidebarNamedFiles must replace self.view with a
    new LazyTreeView instance.  The old view is deleted; the new one is a
    distinct object.
    """
    sidebar = main.sidebar_rt_top
    view_before = sidebar.view
    assert view_before is not None, "Named-files sidebar must have a view before refresh"

    sidebar.refresh()

    assert sidebar.view is not None, "Named-files sidebar must have a view after refresh"
    assert sidebar.view is not view_before, (
        "refresh() must replace self.view with a new instance"
    )


def test_named_paths_refresh_replaces_view(main):
    """
    Calling refresh() on SidebarNamedPaths must replace self.view with a
    new LazyTreeView instance.
    """
    sidebar = main.sidebar_rt_mid
    view_before = sidebar.view
    assert view_before is not None, "Named-paths sidebar must have a view before refresh"

    sidebar.refresh()

    assert sidebar.view is not None, "Named-paths sidebar must have a view after refresh"
    assert sidebar.view is not view_before, (
        "refresh() must replace self.view with a new instance"
    )


def test_archive_refresh_replaces_view(main):
    """
    Calling refresh() on SidebarArchive must replace self.view with a new
    LazyTreeView instance.  On a fresh project (tabs hidden, no runs yet)
    this follows the simpler refresh path in SidebarArchive.refresh().
    """
    sidebar = main.sidebar_rt_bottom
    view_before = sidebar.view
    assert view_before is not None, "Archive sidebar must have a view before refresh"

    sidebar.refresh()

    assert sidebar.view is not None, "Archive sidebar must have a view after refresh"
    assert sidebar.view is not view_before, (
        "refresh() must replace self.view with a new instance"
    )


# ---------------------------------------------------------------------------
# Tests — refresh() picks up content added after initial setup
# ---------------------------------------------------------------------------


def test_named_files_refresh_picks_up_new_entry(main):
    """
    Content added to the named-files backend after the sidebar's initial
    setup must appear in the model after refresh().

    The TreeModel is built once at setup() time — it does not watch for
    changes.  Calling refresh() creates a new TreeModel that reads the
    current backend state, so a newly registered named-file directory
    becomes visible.  Registration may also write a manifest.json at the
    root, so the assertion checks for more entries than before rather than
    a specific count.
    """
    sidebar = main.sidebar_rt_top
    initial_count = sidebar.model.rowCount(QModelIndex())

    # Register a named-file (creates a sub-directory, possibly a manifest.json)
    _register_named_file(main)

    # The old model still reflects the pre-registration state — no auto-update
    assert sidebar.model.rowCount(QModelIndex()) == initial_count, (
        "Old model must not auto-update when a new entry is added"
    )

    sidebar.refresh()

    # The new model reads the current backend state and sees the new content
    assert sidebar.model.rowCount(QModelIndex()) > initial_count, (
        "After refresh(), named-files tree must show more entries than before registration"
    )


def test_named_paths_refresh_picks_up_new_entry(main):
    """
    Content added to the named-paths backend after the sidebar's initial
    setup must appear in the model after refresh().  Registration may also
    write a manifest.json at the root, so the assertion checks for more
    entries than before rather than a specific count.
    """
    sidebar = main.sidebar_rt_mid
    initial_count = sidebar.model.rowCount(QModelIndex())

    # Register a named-paths group (creates a sub-directory, possibly a manifest)
    _register_named_paths(main)

    # The old model still reflects the pre-registration state
    assert sidebar.model.rowCount(QModelIndex()) == initial_count, (
        "Old model must not auto-update when a new entry is added"
    )

    sidebar.refresh()

    # New model reflects the newly registered group (and any metadata files)
    assert sidebar.model.rowCount(QModelIndex()) > initial_count, (
        "After refresh(), named-paths tree must show more entries than before registration"
    )
