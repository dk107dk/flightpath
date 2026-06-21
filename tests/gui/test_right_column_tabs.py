"""
pytest-qt tests for right-column Ops/AI/Help tab-bar visibility.

Checklist coverage:
  HOME > Ops, AI, Help tabs appear when a file is opened
  HOME > Ops, AI, Help tabs hide when no files are open

The right-column QTabWidget's tab bar is shown by rt_tabs_show() and hidden
by rt_tabs_hide().  Both are triggered through Reactor.on_stack_change(),
which listens to main_layout.currentChanged:

  file open → update_*_views() → rt_tabs_show()          → bar visible
  welcome   → main_layout.setCurrentIndex(0)
              → on_stack_change() → rt_tabs_hide()         → bar hidden
  last tab closed → ClosingTabs.close_tab_at()
              → count == 0 → main_layout.setCurrentIndex(0)
              → on_stack_change() → rt_tabs_hide()         → bar hidden

Six document types are exercised (one test each):
  CSV (.csv), XLSX (.xlsx), JSONL (.jsonl), JSON (.json),
  Markdown (.md), and CsvPath (.csvpath).

Run with:
  QT_QPA_PLATFORM=offscreen poetry run python -m pytest tests/gui/test_right_column_tabs.py -v
"""

import os

from flightpath.util.tabs_utility import TabsUtility as taut

# isolated_home and main fixtures are provided by conftest.py

TIMEOUT = 8000  # ms

XLSX_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "test_resources",
    "CPIForecast.xlsx",
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _examples(main, *parts) -> str:
    return os.path.join(main.state.cwd, "examples", *parts)


def _open_and_wait(qtbot, main, path: str) -> None:
    """Open a file and block until its content tab appears."""
    main.read_validate_and_display_file_for_path(path)
    qtbot.waitUntil(
        lambda: taut.find_tab(main.content.tab_widget, path) is not None,
        timeout=TIMEOUT,
    )


def _rt_bar_visible(main) -> bool:
    return main.rt_tab_widget.tabBar().isVisible()


# ---------------------------------------------------------------------------
# Tests — initial state
# ---------------------------------------------------------------------------


def test_rt_tabs_hidden_on_welcome_screen(main):
    """
    On a fresh start (Welcome screen, main_layout index 0), the right-column
    tab bar must be hidden — no file is open yet.
    """
    assert not _rt_bar_visible(main), (
        "Right-column tab bar must be hidden on the Welcome screen"
    )


# ---------------------------------------------------------------------------
# Tests — tab bar appears for each document type
# ---------------------------------------------------------------------------


def test_rt_tabs_appear_after_csv_open(qtbot, main):
    """
    Opening a CSV file must make the right-column tab bar visible.
    CSV files are loaded by GeneralDataWorker → update_data_views → rt_tabs_show().
    """
    _open_and_wait(qtbot, main, _examples(main, "first steps", "test.csv"))
    assert _rt_bar_visible(main), (
        "Right-column tab bar must be visible after opening a CSV file"
    )


def test_rt_tabs_appear_after_xlsx_open(qtbot, main):
    """
    Opening an XLSX file must make the right-column tab bar visible.
    XLSX files follow the same GeneralDataWorker → update_data_views path as CSV.
    """
    _open_and_wait(qtbot, main, XLSX_PATH)
    assert _rt_bar_visible(main), (
        "Right-column tab bar must be visible after opening an XLSX file"
    )


def test_rt_tabs_appear_after_jsonl_open(qtbot, main):
    """
    Opening a JSONL file must make the right-column tab bar visible.
    JSONL is routed through GeneralDataWorker (grid view) → update_data_views.
    """
    _open_and_wait(qtbot, main, _examples(main, "json", "prompts.jsonl"))
    assert _rt_bar_visible(main), (
        "Right-column tab bar must be visible after opening a JSONL file"
    )


def test_rt_tabs_appear_after_json_open(qtbot, main):
    """
    Opening a JSON file must make the right-column tab bar visible.
    JSON files are loaded by JsonWorker → update_json_views → rt_tabs_show().
    """
    _open_and_wait(qtbot, main, _examples(main, "named-paths groups", "my_named_paths.json"))
    assert _rt_bar_visible(main), (
        "Right-column tab bar must be visible after opening a JSON file"
    )


def test_rt_tabs_appear_after_md_open(qtbot, main):
    """
    Opening a Markdown file must make the right-column tab bar visible.
    Markdown files are loaded by MdWorker → update_md_views → rt_tabs_show().
    """
    _open_and_wait(qtbot, main, _examples(main, "first steps", "README.md"))
    assert _rt_bar_visible(main), (
        "Right-column tab bar must be visible after opening a Markdown file"
    )


def test_rt_tabs_appear_after_csvpath_open(qtbot, main):
    """
    Opening a csvpath file must make the right-column tab bar visible.
    Csvpath files are loaded by CsvpathFileWorker → update_csvpath_views → rt_tabs_show().
    """
    _open_and_wait(qtbot, main, _examples(main, "first steps", "Hello World.csvpath"))
    assert _rt_bar_visible(main), (
        "Right-column tab bar must be visible after opening a csvpath file"
    )


# ---------------------------------------------------------------------------
# Tests — tab bar hides when no file is open
# ---------------------------------------------------------------------------


def test_rt_tabs_hide_on_welcome_screen(qtbot, main):
    """
    Calling show_welcome_screen() after a file is open must hide the
    right-column tab bar.  show_welcome_screen() sets main_layout to index 0,
    which triggers Reactor.on_stack_change() → rt_tabs_hide().
    """
    _open_and_wait(qtbot, main, _examples(main, "first steps", "test.csv"))
    assert _rt_bar_visible(main), "Tab bar must be visible before this test is meaningful"

    main.show_welcome_screen()

    assert not _rt_bar_visible(main), (
        "Right-column tab bar must be hidden after returning to the Welcome screen"
    )


def test_rt_tabs_hide_when_last_tab_closed(qtbot, main):
    """
    Closing the last content tab must hide the right-column tab bar.
    ClosingTabs.close_tab_at() detects count == 0 and sets main_layout to
    index 0, triggering Reactor.on_stack_change() → rt_tabs_hide().
    """
    path = _examples(main, "first steps", "test.csv")
    _open_and_wait(qtbot, main, path)
    assert _rt_bar_visible(main), "Tab bar must be visible before this test is meaningful"

    main.content.tab_widget.close_tab(path)

    assert not _rt_bar_visible(main), (
        "Right-column tab bar must be hidden after the last content tab is closed"
    )
