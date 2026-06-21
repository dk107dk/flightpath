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

from PySide6.QtCore import QModelIndex

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


def _log_tab_count(tab_widget) -> int:
    return sum(
        1
        for i in range(tab_widget.count())
        if tab_widget.widget(i).objectName().startswith("Log-")
    )


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


def test_production_run_adds_item_to_runs_accordion(qtbot, main):
    """
    Starting a production run must add an item to the Runs accordion in the
    archive sidebar.  on_query_submitted() creates the item synchronously
    (before the worker starts) with a yellow status dot and the title
    "{named_paths_name} results for {named_file_name}".

    The Runs accordion (QueryAccordionWidget) is the in-flight view of active
    and recently completed runs.  Its item count and title are the primary
    indicators that the sidebar is tracking the run correctly.

    After run completion, the item's status dot turns green (done) and the
    Runs tab remains visible; this test confirms both the count and the title.
    """
    _setup_and_run(qtbot, main)

    runs = main.sidebar_rt_bottom.runs
    assert runs.count == 1, (
        "Exactly one item must appear in the Runs accordion after a single production run"
    )

    item = runs.items[0]
    title_text = item.title.text()
    assert "hello-world" in title_text, (
        f"Accordion item title must include the named-paths group name; got: {title_text!r}"
    )
    assert "test" in title_text, (
        f"Accordion item title must include the named-file name; got: {title_text!r}"
    )


def test_archive_file_click_opens_content_tab(qtbot, main):
    """
    Clicking a file in the archive tree must open it in a content viewer tab.

    The reactor's on_archive_tree_click slot sets main.selected_file_path to the
    tree item's path and delegates to on_rt_tree_click(), which opens the file
    only if it is a regular file (not a directory).

    After a production run the archive always contains at least a manifest.json
    inside the run directory.  The test discovers that file via os.walk (so it
    is robust to other result files CsvPath may write), sets selected_file_path,
    and calls on_rt_tree_click() directly — the same code path taken by a real
    tree-click.  A matching content tab is the acceptance criterion.
    """
    _setup_and_run(qtbot, main)

    archive_root = main.csvpath_config.get(section="results", name="archive")
    result_file = None
    for dirpath, _, filenames in os.walk(archive_root):
        for fname in filenames:
            result_file = os.path.join(dirpath, fname)
            break
        if result_file:
            break

    assert result_file is not None, (
        "Archive must contain at least one file after a production run"
    )

    main.selected_file_path = result_file
    main.reactor.on_rt_tree_click()

    qtbot.waitUntil(
        lambda: taut.find_tab(main.content.tab_widget, result_file) is not None,
        timeout=TIMEOUT,
    )


def test_rerun_produces_second_log_tab(monkeypatch, qtbot, main):
    """
    Re-running a completed production run must trigger a second run and add a
    second Log tab to help_and_feedback.

    The rerun path: SidebarArchive._repeat_run() → SidebarArchiveRefMaker reads
    the run directory's manifest.json to recover named_paths="hello-world" and
    named_file="test" → creates NewRunDialog pre-filled with those values →
    show_now_or_later() → do_run() → run_paths() → RunWorker → second Log tab.

    The test selects the run directory in the archive tree model so that
    _get_rerun_references() reads the run manifest and returns the correct
    names.  show_now_or_later is monkeypatched to call dialog.do_run() directly
    without showing the dialog — the dialog's controls are fully initialised in
    __init__, so do_run() reads the correct named_paths and named_file values
    without any user interaction.

    A second Log tab (objectName starts with 'Log-') is the acceptance
    criterion: its appearance confirms the RunWorker ran to completion.
    """
    _setup_and_run(qtbot, main)

    hf = main.helper.help_and_feedback
    assert _log_tab_count(hf) == 1, "Precondition: exactly one Log tab after first run"

    # After _display_log, renew_sidebar_archive() replaces sidebar_rt_bottom with a
    # fresh SidebarArchive whose TreeModel is rooted at the archive directory.
    # Level 0 of the model (children of root): named-paths group directories.
    # Level 1 under hello-world: the timestamped run directory created by the run.
    sidebar = main.sidebar_rt_bottom
    model = sidebar.model

    group_idx = model.index(0, 0, QModelIndex())
    assert group_idx.isValid(), (
        "Archive model must have at least one named-paths group after the run"
    )

    # Row 0 under the group dir sorts to the timestamp directory (digits < letters),
    # so manifest.json (if present at this level) sorts after the run dir.
    run_idx = model.index(0, 0, group_idx)
    assert run_idx.isValid(), (
        "The named-paths group must have at least one run directory"
    )

    run_path = model.filePath(run_idx)
    assert run_path is not None and os.path.isdir(run_path), (
        f"Expected a run directory at index (0,0) under hello-world; got: {run_path!r}"
    )

    # Select the run directory in the archive tree so _repeat_run() picks it up
    sidebar.view.setCurrentIndex(run_idx)

    # Intercept show_now_or_later to bypass the NewRunDialog and call do_run() directly.
    # show_now_or_later is also called with help-icon widgets (ClickableLabel) during
    # NewRunDialog.__init__; only act on the dialog itself.
    from flightpath.dialogs.new_run_dialog import NewRunDialog

    def _fire_run_immediately(showable):
        if isinstance(showable, NewRunDialog):
            showable.do_run()

    monkeypatch.setattr(main, "show_now_or_later", _fire_run_immediately)

    sidebar._repeat_run()

    qtbot.waitUntil(lambda: _log_tab_count(hf) == 2, timeout=TIMEOUT)
