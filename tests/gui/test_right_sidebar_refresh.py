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
    An external filesystem change to the named-files directory must not be
    visible in the sidebar until refresh() is called.

    The sidebar's TreeModel is built once at setup() and does not watch the
    filesystem for changes — this is intentional, since the named-files
    directory may be on S3, Azure Blob, SFTP, or another non-local backend
    that cannot be watched cheaply.  refresh() tears down the old TreeModel
    and builds a fresh one from the current backend state.

    The test creates a directory directly under the named-files root with
    os.makedirs(), bypassing the FlightPath registration API entirely.  This
    simulates the real refresh use-case: a change made by another FlightPath
    instance, a CI pipeline, or a direct filesystem tool that the running app
    has no knowledge of.  Because only one known directory is added, the
    assertion can be exact (initial_count + 1) rather than the weaker '>'.
    """
    sidebar = main.sidebar_rt_top
    initial_count = sidebar.model.rowCount(QModelIndex())

    # Add a directory directly to the filesystem, bypassing the FlightPath API
    external_dir = os.path.join(_inputs_files_root(main), "external_group")
    os.makedirs(external_dir)

    # The old model is blind to the external change — no auto-update
    assert sidebar.model.rowCount(QModelIndex()) == initial_count, (
        "Sidebar model must not auto-update when a directory is added externally"
    )

    sidebar.refresh()

    # After rebuild the new directory is visible — exactly one more entry
    assert sidebar.model.rowCount(QModelIndex()) == initial_count + 1, (
        "After refresh(), named-files tree must show exactly one new entry "
        "for the externally created directory"
    )


def test_named_paths_refresh_picks_up_new_entry(main):
    """
    An external filesystem change to the named-paths directory must not be
    visible in the sidebar until refresh() is called.

    Mirrors test_named_files_refresh_picks_up_new_entry: a directory is
    created directly under the named-paths root via os.makedirs(), and the
    test verifies that refresh() — not the registration API — is what makes
    it appear.  The exact count assertion (initial_count + 1) is possible
    because only one known directory is added.
    """
    sidebar = main.sidebar_rt_mid
    initial_count = sidebar.model.rowCount(QModelIndex())

    # Add a directory directly to the filesystem, bypassing the FlightPath API
    external_dir = os.path.join(_inputs_csvpaths_root(main), "external_group")
    os.makedirs(external_dir)

    # The old model is blind to the external change
    assert sidebar.model.rowCount(QModelIndex()) == initial_count, (
        "Sidebar model must not auto-update when a directory is added externally"
    )

    sidebar.refresh()

    # After rebuild the new directory is visible — exactly one more entry
    assert sidebar.model.rowCount(QModelIndex()) == initial_count + 1, (
        "After refresh(), named-paths tree must show exactly one new entry "
        "for the externally created directory"
    )
