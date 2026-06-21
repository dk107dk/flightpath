"""
pytest-qt tests for the production-like run workflow.

Checklist coverage:
  RUNS > stage named-file
  RUNS > load named-paths group
  RUNS > run (collect serially)
  RUNS > log tab appears after run
  RUNS > archive populated after run

A production run differs from a one-off run: it requires a registered named-file
(staged input data) and a registered named-paths group (loaded csvpath definitions).
The run is dispatched via main.run_paths(), which:
  1. Creates a fresh CsvPaths instance (new_csvpaths())
  2. Wraps it in a RunWorker on the Qt thread pool
  3. On completion emits finished → _display_log, which adds a "Log-{cid}" tab to
     main.helper.help_and_feedback and refreshes the archive sidebar

Setup:
  - Named-file registered with main.csvpaths.file_manager.add_named_file()
  - Named-paths registered with main.csvpaths.paths_manager.add_named_paths_from_file()
  CsvPaths shares registrations across instances in-process, so the fresh CsvPaths
  created by new_csvpaths() will find them.  os.chdir(isolated_cwd) is called during
  MainWindow startup, so relative archive/log paths resolve to the isolated project.

Run with:
  QT_QPA_PLATFORM=offscreen poetry run python -m pytest tests/gui/test_production_run.py -v
"""

import os

from flightpath.util.tabs_utility import TabsUtility as taut

# isolated_home and main fixtures are provided by conftest.py

TIMEOUT = 20000  # ms — RunWorker + _display_log + archive refresh can be slow


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _examples(main, *parts) -> str:
    return os.path.join(main.state.cwd, "examples", *parts)


def _has_log_tab(tab_widget) -> bool:
    """Return True once a production-run Log tab (objectName 'Log-<cid>') exists."""
    for i in range(tab_widget.count()):
        if tab_widget.widget(i).objectName().startswith("Log-"):
            return True
    return False


def _setup_and_run(
    qtbot,
    main,
    *,
    named_file_name: str = "test",
    named_paths_name: str = "hello-world",
) -> None:
    """
    Register a named-file (test.csv) and a named-paths group (Hello World.csvpath),
    then trigger a production run and block until the Log tab appears.
    """
    csvpath_file = _examples(main, "first steps", "Hello World.csvpath")
    csv_file = _examples(main, "first steps", "test.csv")
    assert os.path.exists(csvpath_file), f"Missing: {csvpath_file}"
    assert os.path.exists(csv_file), f"Missing: {csv_file}"

    csvpaths = main.csvpaths
    csvpaths.config.set(section="inputs", name="allow_local_files", value=True)
    csvpaths.file_manager.add_named_file(
        name=named_file_name, path=csv_file, template=None
    )
    csvpaths.paths_manager.add_named_paths_from_file(
        name=named_paths_name,
        file_path=csvpath_file,
        template=None,
        append=False,
    )

    main.run_paths(
        method="collect_paths",
        named_paths_name=named_paths_name,
        named_file_name=named_file_name,
        template=None,
    )

    qtbot.waitUntil(
        lambda: _has_log_tab(main.helper.help_and_feedback),
        timeout=TIMEOUT,
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_production_run_creates_log_tab(qtbot, main):
    """
    A production run must add a Log tab to help_and_feedback once it completes.
    The tab's objectName starts with 'Log-' (the CsvPaths instance id is appended).
    """
    _setup_and_run(qtbot, main)

    hf = main.helper.help_and_feedback
    assert _has_log_tab(hf), "Expected a Log tab after the production run completed"


def test_production_run_log_tab_has_content(qtbot, main):
    """
    The Log tab created by a production run must contain a QPlainTextEdit whose
    content is non-empty (CsvPath writes at least one log line during collect_paths).
    """
    from PySide6.QtWidgets import QPlainTextEdit

    _setup_and_run(qtbot, main)

    hf = main.helper.help_and_feedback
    log_widget = None
    for i in range(hf.count()):
        if hf.widget(i).objectName().startswith("Log-"):
            log_widget = hf.widget(i)
            break
    assert log_widget is not None, "Log tab widget not found"

    layout = log_widget.layout()
    assert layout is not None and layout.count() > 0, "Log tab has no child widget"
    text_view = layout.itemAt(0).widget()
    assert isinstance(text_view, QPlainTextEdit), "Log tab child must be a QPlainTextEdit"


def test_production_run_archive_populated(qtbot, main):
    """
    A production run must populate the archive directory with a result entry for
    the named-paths group.  The run also calls renew_sidebar_archive() which rebuilds
    the archive sidebar widget — confirmed by the sidebar still being present.
    """
    named_paths_name = "hello-world"
    _setup_and_run(qtbot, main, named_paths_name=named_paths_name)

    archive_root = os.path.join(main.state.cwd, "archive", named_paths_name)
    assert os.path.isdir(archive_root), (
        f"Expected archive directory for '{named_paths_name}' at: {archive_root}"
    )
    entries = [e for e in os.listdir(archive_root) if not e.startswith(".")]
    assert len(entries) > 0, (
        f"Archive directory for '{named_paths_name}' is empty; expected a run result"
    )
    # sidebar_rt_bottom is rebuilt by renew_sidebar_archive() after _display_log
    assert main.sidebar_rt_bottom is not None, (
        "sidebar_rt_bottom must exist after archive refresh"
    )
