"""
pytest-qt tests for the EXAMPLES section of the checklist.

Checklist coverage:
  EXAMPLES > run through the examples
  EXAMPLES > large file warning — open dups.csvpaths (> 1 MB) triggers warning dialog
  EXAMPLES > auto-add `test-data:` path directive

== Run through examples ==

A curated set of single-block example csvpaths (each with exactly one
test-data: directive) is run parametrically via run_one_csvpath_2().  The
test opens each file in a CsvpathViewer, reads its text, resolves the data
file path relative to cwd, and calls run_one_csvpath_2() directly — the same
path taken by Ctrl-R / right-click Run in the live app.

Result-tab presence (Log, Why) is the acceptance criterion: if either is
missing the run failed silently.

Examples covered:
  first steps/Hello World.csvpath     — test.csv (3 rows)  print output
  first steps/simple_model.csvpath    — test.csv (3 rows)  line() schema
  counting/summing.csvpath            — projects.csv (18 rows)  sum()
  counting/temps.csvpath              — temps.txt (15 lines)  average per month

== Large file warning ==

run_one_csvpath_2() checks os.path.getsize(filepath) before executing.
If size >= 1,000,000 bytes it calls meut.yesNo2() with title "Large file"
and returns — the run does not start.

The Alzheimers_Disease_and_Healthy_Aging_Data_sample.csv file (≈2 MB, 5 000
rows) is the data file used by dups.csvpaths in the examples.  The test
patches MessageUtility.yesNo2 to capture the call without blocking and
asserts the title matches.

== Auto-add test-data: ==

When a csvpath with no test-data: directive is run, run_one_csvpath_2()
calls CsvPathTextEdit.add_to_external_comment_of_csvpath_at_position() to
write `test-data:{filepath}` into the editor comment, saving the user from
being prompted again next time.

The test creates a minimal csvpath file without test-data:, opens it, runs
it with test.csv, and asserts the editor text now contains "test-data:".

Run with:
  QT_QPA_PLATFORM=offscreen poetry run python -m pytest tests/gui/test_examples.py -v
"""

import os

import pytest

from flightpath.util.message_utility import MessageUtility
from flightpath.util.tabs_utility import TabsUtility as taut
from flightpath.widgets.panels.csvpath_viewer import CsvpathViewer

# isolated_home and main fixtures are provided by conftest.py

TIMEOUT = 20000  # ms — examples may be slower than Hello World


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _examples(main, *parts) -> str:
    return os.path.join(main.state.cwd, "examples", *parts)


def _open_csvpath(qtbot, main, path: str) -> CsvpathViewer:
    """Open a csvpath file and block until its CsvpathViewer tab appears."""
    main.read_validate_and_display_file_for_path(path)
    qtbot.waitUntil(
        lambda: taut.find_tab(main.content.tab_widget, path) is not None,
        timeout=TIMEOUT,
    )
    viewer = taut.find_tab(main.content.tab_widget, path)[1]
    assert isinstance(viewer, CsvpathViewer), f"Expected CsvpathViewer for {path}"
    return viewer


def _has_tab(tab_widget, object_name: str) -> bool:
    return taut.find_tab(tab_widget, object_name) is not None


# ---------------------------------------------------------------------------
# Tests — run through examples (parametrized)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "csvpath_rel, data_rel",
    [
        ("first steps/Hello World.csvpath", "first steps/test.csv"),
        ("first steps/simple_model.csvpath", "first steps/test.csv"),
        ("counting/summing.csvpath", "counting/projects.csv"),
        ("counting/temps.csvpath", "counting/temps.txt"),
    ],
    ids=["hello_world", "simple_model", "summing", "temps"],
)
def test_example_run_creates_log_and_why_tabs(qtbot, main, csvpath_rel, data_rel):
    """
    Each example csvpath must produce at least a Log tab and a Why tab when
    run via run_one_csvpath_2().

    Log appears after _run_feedback() completes; Why is always written.
    Missing either indicates the run failed silently — a regression in
    CsvPath integration, the worker plumbing, or result-tab construction.

    The test passes the absolute data path directly to run_one_csvpath_2(),
    which is the same path taken by Ctrl-R once a test-data: directive is
    present — no file-picker dialog is needed.
    """
    csvpath_path = _examples(main, *csvpath_rel.split("/"))
    data_path = _examples(main, *data_rel.split("/"))
    assert os.path.exists(csvpath_path), f"Example missing: {csvpath_path}"
    assert os.path.exists(data_path), f"Data file missing: {data_path}"

    viewer = _open_csvpath(qtbot, main, csvpath_path)
    csvpath_text = viewer.text_edit.toPlainText()

    viewer.run_one.run_one_csvpath_2(data_path, csvpath=csvpath_text)

    hf = main.helper.help_and_feedback
    qtbot.waitUntil(lambda: _has_tab(hf, "Log"), timeout=TIMEOUT)
    assert _has_tab(hf, "Why"), (
        f"'Why' tab must appear after running {csvpath_rel}"
    )


# ---------------------------------------------------------------------------
# Tests — large file warning
# ---------------------------------------------------------------------------


def test_large_file_triggers_warning_dialog(monkeypatch, qtbot, main):
    """
    Attempting to run a csvpath against a data file >= 1 MB must trigger a
    yesNo2 warning with title 'Large file' before the run starts.

    run_one_csvpath_2() calls os.path.getsize(filepath) after parsing the
    csvpath; if size >= 1,000,000 it fires meut.yesNo2() and returns
    without starting the OneOffRunWorker.

    The Alzheimers data file (≈2 MB, 5 000 rows) is used because it is the
    data file referenced by dups.csvpaths in the examples — the canonical
    large-file example in the app.

    MessageUtility.yesNo2 is monkeypatched to capture the call and NOT invoke
    the callback, so no run is started and the test finishes quickly.
    """
    alz_path = _examples(
        main,
        "duplicates",
        "Alzheimers_Disease_and_Healthy_Aging_Data_sample.csv",
    )
    assert os.path.exists(alz_path), f"Alzheimers data file missing: {alz_path}"
    assert os.path.getsize(alz_path) >= 1_000_000, (
        "Alzheimers file must be >= 1 MB to trigger the large file warning"
    )

    # Open any valid csvpath to get a CsvpathViewer with run_one attached
    csvpath_path = _examples(main, "first steps", "Hello World.csvpath")
    viewer = _open_csvpath(qtbot, main, csvpath_path)
    csvpath_text = viewer.text_edit.toPlainText()

    # Capture the yesNo2 call without invoking the run callback
    warnings = []

    def _fake_yes_no2(*, parent, msg, title="", callback, args=None):
        warnings.append({"title": title, "msg": msg})

    monkeypatch.setattr(MessageUtility, "yesNo2", _fake_yes_no2)

    viewer.run_one.run_one_csvpath_2(alz_path, csvpath=csvpath_text)

    assert len(warnings) == 1, (
        f"Exactly one large-file warning must fire; got {len(warnings)}"
    )
    assert warnings[0]["title"] == "Large file", (
        f"Warning title must be 'Large file'; got {warnings[0]['title']!r}"
    )


# ---------------------------------------------------------------------------
# Tests — auto-add test-data: directive
# ---------------------------------------------------------------------------


def test_run_without_test_data_adds_directive_to_editor(qtbot, main):
    """
    Running a csvpath that has no test-data: directive must add
    `test-data:{filepath}` to the csvpath comment in the editor.

    run_one_csvpath_2() detects the missing directive and calls
    CsvPathTextEdit.add_to_external_comment_of_csvpath_at_position(), which
    updates the editor text synchronously before the run worker starts.

    The updated text persists in the editor so the user sees the new directive
    and is not prompted for a file on subsequent runs.

    The test writes a minimal csvpath (no test-data:) to the project, opens
    it, runs it with test.csv as data, and asserts the editor now contains
    "test-data:".  The run is allowed to complete — the csvpath is trivial
    (1 line, print output) and the data file is 3 rows.
    """
    # Create a minimal csvpath without a test-data: directive
    csvpath_content = "~\n name: no-data-directive\n~\n$[1][ print(\"auto-add test\") ]\n"
    csvpath_path = os.path.join(main.state.cwd, "no_test_data.csvpath")
    with open(csvpath_path, "w") as f:
        f.write(csvpath_content)

    data_path = _examples(main, "first steps", "test.csv")
    assert os.path.exists(data_path), f"test.csv missing: {data_path}"

    viewer = _open_csvpath(qtbot, main, csvpath_path)

    # Confirm the editor does not yet contain test-data:
    original_text = viewer.text_edit.toPlainText()
    assert "test-data:" not in original_text, (
        "Precondition: editor must not contain test-data: before the run"
    )

    # Run — position=0 simulates cursor at start of document
    viewer.run_one.run_one_csvpath_2(data_path, csvpath=original_text, position=0)

    # The directive is added synchronously before the worker starts
    updated_text = viewer.text_edit.toPlainText()
    assert "test-data:" in updated_text, (
        "After run_one_csvpath_2(), the editor must contain a test-data: directive"
    )
    assert os.path.basename(data_path) in updated_text or data_path in updated_text, (
        "The added test-data: directive must reference the data file path"
    )

    # Wait for the run to complete (Log tab confirms the worker finished)
    qtbot.waitUntil(
        lambda: _has_tab(main.helper.help_and_feedback, "Log"),
        timeout=TIMEOUT,
    )
