"""
pytest-qt tests for JSONL file viewing: grid→text toggle and expand/collapse.

Two behaviours are covered:

1. ctrl-t grid→text toggle
   When a .jsonl file is open in a DataViewer (grid), pressing ctrl-t (or
   calling reactor.on_raw_source()) must close the DataViewer tab and reopen
   the same path in a JsonViewer2 text editor.

   The fix: reactor.on_raw_source() called self.main.sidebar._do_edit_as_json()
   but the method had been moved to sidebar.actions.  The one-line fix changes
   the call to self.main.sidebar.actions._do_edit_as_json(path).

2. JSONL expand / collapse within JsonViewer2
   A .jsonl file in JsonViewer2 shows one compact JSON object per line
   (_expanded == False).  Calling _expand() must pretty-print each JSON
   object across multiple lines (_expanded == True).  Calling _expand() a
   second time must contract the view back to one object per line
   (_expanded == False).

Run with:
  QT_QPA_PLATFORM=offscreen poetry run python -m pytest tests/gui/test_jsonl_views.py -v
"""

import os

from flightpath.util.tabs_utility import TabsUtility as taut
from flightpath.widgets.panels.data_viewer import DataViewer
from flightpath.widgets.panels.json_viewer_2 import JsonViewer2

# isolated_home and main fixtures are provided by conftest.py

TIMEOUT = 8000  # ms — background workers run on the Qt thread pool


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _examples(main, *parts) -> str:
    return os.path.join(main.state.cwd, "examples", *parts)


def _jsonl_path(main) -> str:
    return _examples(main, "json", "prompts.jsonl")


def _open_jsonl_as_grid(qtbot, main) -> DataViewer:
    """Open the example prompts.jsonl in the default grid (DataViewer) view."""
    path = _jsonl_path(main)
    assert os.path.exists(path), f"Example JSONL missing: {path}"
    main.read_validate_and_display_file_for_path(path)
    qtbot.waitUntil(
        lambda: taut.find_tab(main.content.tab_widget, path) is not None,
        timeout=TIMEOUT,
    )
    viewer = taut.find_tab(main.content.tab_widget, path)[1]
    assert isinstance(viewer, DataViewer), (
        f"prompts.jsonl must open as DataViewer; got {type(viewer).__name__}"
    )
    return viewer


def _open_jsonl_as_text(qtbot, main) -> JsonViewer2:
    """Open the example prompts.jsonl directly in JsonViewer2 (text view)."""
    path = _jsonl_path(main)
    assert os.path.exists(path), f"Example JSONL missing: {path}"
    main.sidebar.actions._do_edit_as_json(path)
    qtbot.waitUntil(
        lambda: taut.find_tab(main.content.tab_widget, path) is not None,
        timeout=TIMEOUT,
    )
    qtbot.wait(2000)  # allow the JsonDataWorker to fully populate the view
    viewer = taut.find_tab(main.content.tab_widget, path)[1]
    assert isinstance(viewer, JsonViewer2), (
        f"_do_edit_as_json must produce a JsonViewer2; got {type(viewer).__name__}"
    )
    return viewer


# ---------------------------------------------------------------------------
# Tests — ctrl-t grid→text toggle
# ---------------------------------------------------------------------------


def test_jsonl_opens_as_data_viewer(qtbot, main):
    """
    Opening a .jsonl file with read_validate_and_display_file_for_path must
    produce a DataViewer (grid) tab, not a text editor.

    This is the baseline for the toggle test: ctrl-t switches away from this
    default grid view.
    """
    path = _jsonl_path(main)
    viewer = _open_jsonl_as_grid(qtbot, main)

    assert isinstance(viewer, DataViewer), (
        f"prompts.jsonl must open as DataViewer by default; got {type(viewer).__name__}"
    )
    assert taut.find_tab(main.content.tab_widget, path) is not None, (
        "A tab for the JSONL file must exist after opening"
    )


def test_ctrl_t_on_jsonl_opens_json_viewer2(qtbot, main):
    """
    With a .jsonl file open in a DataViewer, calling reactor.on_raw_source()
    (the ctrl-t handler) must close the DataViewer tab and open the same path
    in a JsonViewer2 text editor.

    The fix corrected the call-site in on_raw_source() from
    'sidebar._do_edit_as_json' to 'sidebar.actions._do_edit_as_json', which
    is where the method now lives after a refactor.
    """
    path = _jsonl_path(main)
    _open_jsonl_as_grid(qtbot, main)

    # Make the DataViewer tab the active tab so on_raw_source() reads the right path
    tab_idx, _ = taut.find_tab(main.content.tab_widget, path)
    main.content.tab_widget.setCurrentIndex(tab_idx)

    # Trigger the ctrl-t toggle path
    main.reactor.on_raw_source()

    # DataViewer is closed synchronously; JsonViewer2 arrives via background worker
    qtbot.waitUntil(
        lambda: taut.find_tab(main.content.tab_widget, path) is not None,
        timeout=TIMEOUT,
    )
    qtbot.wait(2000)

    viewer = taut.find_tab(main.content.tab_widget, path)[1]
    assert isinstance(viewer, JsonViewer2), (
        f"ctrl-t on a JSONL DataViewer must produce a JsonViewer2; "
        f"got {type(viewer).__name__}"
    )


# ---------------------------------------------------------------------------
# Tests — JSONL expand / collapse within JsonViewer2
# ---------------------------------------------------------------------------


def test_jsonl_viewer_starts_unexpanded(qtbot, main):
    """
    When a .jsonl file is first opened in JsonViewer2 via _do_edit_as_json,
    _expanded must be False — content is shown as one compact JSON object
    per line.
    """
    viewer = _open_jsonl_as_text(qtbot, main)
    assert viewer._expanded is False, (
        "JsonViewer2 must start with _expanded=False for a .jsonl file"
    )


def test_jsonl_expand_prettifies_content(qtbot, main):
    """
    Calling _expand() on a JsonViewer2 showing .jsonl content must
    pretty-print each JSON object across multiple lines and set
    _expanded=True.

    In compact JSONL form each JSON object occupies one line.  After
    expansion each occupies several lines (nested keys are indented), so
    the expanded view must have more non-empty lines than the original.
    """
    viewer = _open_jsonl_as_text(qtbot, main)

    initial_text = viewer.view.toPlainText()
    initial_lines = [ln for ln in initial_text.split("\n") if ln.strip()]
    assert len(initial_lines) > 0, "JSONL viewer must have content before expansion"

    viewer._expand()

    assert viewer._expanded is True, "_expanded must be True after the first _expand() call"
    expanded_text = viewer.view.toPlainText()
    expanded_lines = [ln for ln in expanded_text.split("\n") if ln.strip()]
    assert len(expanded_lines) > len(initial_lines), (
        f"Expanded JSONL must have more lines than compact; "
        f"compact={len(initial_lines)}, expanded={len(expanded_lines)}"
    )


def test_jsonl_expand_twice_contracts_back(qtbot, main):
    """
    Calling _expand() a second time on an already-expanded JsonViewer2 must
    contract the content back to compact JSONL (one object per line) and set
    _expanded=False.
    """
    viewer = _open_jsonl_as_text(qtbot, main)

    initial_lines = len(
        [ln for ln in viewer.view.toPlainText().split("\n") if ln.strip()]
    )
    assert initial_lines > 0, "Precondition: JSONL viewer must have content"

    viewer._expand()
    assert viewer._expanded is True, "Precondition: must be expanded before contraction"

    expanded_lines = len(
        [ln for ln in viewer.view.toPlainText().split("\n") if ln.strip()]
    )
    assert expanded_lines > initial_lines, (
        "Precondition: expanded view must have more lines than compact"
    )

    viewer._expand()  # contract

    assert viewer._expanded is False, "_expanded must be False after the second _expand() call"
    contracted_lines = len(
        [ln for ln in viewer.view.toPlainText().split("\n") if ln.strip()]
    )
    assert contracted_lines < expanded_lines, (
        f"Contracted JSONL must have fewer lines than expanded; "
        f"expanded={expanded_lines}, contracted={contracted_lines}"
    )
    assert contracted_lines == initial_lines, (
        f"Contracted JSONL must be back to the original line count ({initial_lines}); "
        f"got {contracted_lines}"
    )
