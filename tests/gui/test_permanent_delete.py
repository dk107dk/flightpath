"""
pytest-qt tests for permanent delete of named-files, named-paths, and archive results.

Checklist coverage:
  RUNS > permanent delete > named-files
  RUNS > permanent delete > named-paths
  RUNS > permanent delete > archive

All three right-panel sidebars (SidebarNamedFiles, SidebarNamedPaths, SidebarArchive)
inherit _do_delete_item() from SidebarRightBase, which calls Nos.remove() on the
target path and then invokes a callback to rebuild the relevant sidebar.

Tests call _do_delete_item() directly with QMessageBox.Yes to bypass the yesNo2
confirmation dialog and the tree-index lookup in _delete_item().

Sidebars:
  main.sidebar_rt_top    — SidebarNamedFiles
  main.sidebar_rt_mid    — SidebarNamedPaths
  main.sidebar_rt_bottom — SidebarArchive

Config keys used to find the on-disk paths:
  [inputs]  files     → named_files root
  [inputs]  csvpaths  → named_paths root
  [results] archive   → archive root

Run with:
  QT_QPA_PLATFORM=offscreen poetry run python -m pytest tests/gui/test_permanent_delete.py -v
"""

import os

from PySide6.QtWidgets import QMessageBox

# isolated_home and main fixtures are provided by conftest.py

TIMEOUT = 20000  # ms — production run worker needed for archive test


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _examples(main, *parts) -> str:
    return os.path.join(main.state.cwd, "examples", *parts)


def _inputs_files_root(main) -> str:
    return main.csvpath_config.get(section="inputs", name="files")


def _inputs_csvpaths_root(main) -> str:
    return main.csvpath_config.get(section="inputs", name="csvpaths")


def _archive_root(main) -> str:
    return main.csvpath_config.get(section="results", name="archive")


def _register_named_file(main, name: str = "test") -> str:
    """Register test.csv as a named-file; return the on-disk directory path."""
    csv_file = _examples(main, "first steps", "test.csv")
    csvpaths = main.csvpaths
    csvpaths.config.set(section="inputs", name="allow_local_files", value=True)
    csvpaths.file_manager.add_named_file(name=name, path=csv_file, template=None)
    return os.path.join(_inputs_files_root(main), name)


def _register_named_paths(main, name: str = "hello-world") -> str:
    """Register Hello World.csvpath as a named-paths group; return on-disk directory."""
    csvpath_file = _examples(main, "first steps", "Hello World.csvpath")
    csvpaths = main.csvpaths
    csvpaths.config.set(section="inputs", name="allow_local_files", value=True)
    csvpaths.paths_manager.add_named_paths_from_file(
        name=name, file_path=csvpath_file, template=None, append=False
    )
    return os.path.join(_inputs_csvpaths_root(main), name)


def _run_and_wait(qtbot, main, named_file_name="test", named_paths_name="hello-world"):
    """Register, run, and wait for the Log tab that signals completion."""
    _register_named_file(main, name=named_file_name)
    _register_named_paths(main, name=named_paths_name)
    main.run_paths(
        method="collect_paths",
        named_paths_name=named_paths_name,
        named_file_name=named_file_name,
        template=None,
    )
    qtbot.waitUntil(
        lambda: any(
            main.helper.help_and_feedback.widget(i).objectName().startswith("Log-")
            for i in range(main.helper.help_and_feedback.count())
        ),
        timeout=TIMEOUT,
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_permanent_delete_named_file(main):
    """
    Permanent-deleting a named-file must remove its directory from
    inputs/named_files/ and trigger renew_sidebar_named_files so the
    named-files sidebar is rebuilt.
    """
    named_file_dir = _register_named_file(main)
    assert os.path.isdir(named_file_dir), f"Named-file dir not created: {named_file_dir}"

    main.sidebar_rt_top._do_delete_item(
        QMessageBox.Yes,
        path=named_file_dir,
        callback=main.renew_sidebar_named_files,
    )

    assert not os.path.exists(named_file_dir), (
        f"Named-file directory must be gone after permanent delete: {named_file_dir}"
    )
    assert main.sidebar_rt_top is not None, (
        "sidebar_rt_top must be rebuilt by renew_sidebar_named_files callback"
    )


def test_permanent_delete_named_paths(main):
    """
    Permanent-deleting a named-paths group must remove its directory from
    inputs/named_paths/ and trigger renew_sidebar_named_paths so the
    named-paths sidebar is rebuilt.
    """
    named_paths_dir = _register_named_paths(main)
    assert os.path.isdir(named_paths_dir), (
        f"Named-paths dir not created: {named_paths_dir}"
    )

    main.sidebar_rt_mid._do_delete_item(
        QMessageBox.Yes,
        path=named_paths_dir,
        callback=main.renew_sidebar_named_paths,
    )

    assert not os.path.exists(named_paths_dir), (
        f"Named-paths directory must be gone after permanent delete: {named_paths_dir}"
    )
    assert main.sidebar_rt_mid is not None, (
        "sidebar_rt_mid must be rebuilt by renew_sidebar_named_paths callback"
    )


def test_permanent_delete_archive_result(qtbot, main):
    """
    Permanent-deleting an archive results directory must remove the run results
    from disk and trigger renew_sidebar_archive so the archive sidebar is rebuilt.

    A production run is executed first to create the archive entry.  The entire
    named-paths results directory (archive/{named_paths_name}/) is deleted —
    the same operation a user performs when clearing all results for a group.
    """
    named_paths_name = "hello-world"
    _run_and_wait(qtbot, main, named_paths_name=named_paths_name)

    archive_group_dir = os.path.join(_archive_root(main), named_paths_name)
    assert os.path.isdir(archive_group_dir), (
        f"Archive group directory not found after run: {archive_group_dir}"
    )

    main.sidebar_rt_bottom._do_delete_item(
        QMessageBox.Yes,
        path=archive_group_dir,
        callback=main.renew_sidebar_archive,
    )

    assert not os.path.exists(archive_group_dir), (
        f"Archive directory must be gone after permanent delete: {archive_group_dir}"
    )
    assert main.sidebar_rt_bottom is not None, (
        "sidebar_rt_bottom must be rebuilt by renew_sidebar_archive callback"
    )
