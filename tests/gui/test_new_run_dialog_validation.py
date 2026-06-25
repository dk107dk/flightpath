"""
Tests that NewRunDialog.do_run() validates group.csvpaths before starting a run.

When a named-paths group's group.csvpaths contains an invalid csvpath (e.g. a
match-only expression without a root '$' or scan part), do_run() must:
  - show a warning dialog explaining the problem
  - NOT call main.run_paths()

This catches groups that were registered before the load-time validator was
added, or whose group.csvpaths was edited directly on disk.

Run with:
  QT_QPA_PLATFORM=offscreen poetry run python -m pytest tests/gui/test_new_run_dialog_validation.py -v
"""

import os

import pytest

from flightpath.dialogs.new_run_dialog import NewRunDialog
from flightpath.util.message_utility import MessageUtility as meut

TIMEOUT = 5000  # ms


def _register_hello_world(main):
    """Register the 'hello-world' named-paths group and 'test' named-file."""
    csv_file = os.path.join(main.state.cwd, "examples", "first steps", "test.csv")
    csvpath_file = os.path.join(
        main.state.cwd, "examples", "first steps", "Hello World.csvpath"
    )
    csvpaths = main.csvpaths
    csvpaths.config.set(section="inputs", name="allow_local_files", value=True)
    csvpaths.file_manager.add_named_file(name="test", path=csv_file, template=None)
    csvpaths.paths_manager.add_named_paths_from_file(
        name="hello-world", file_path=csvpath_file, template=None, append=False
    )


def _group_csvpaths_path(main, group_name: str) -> str:
    named_paths_rel = main.csvpath_config.get(section="inputs", name="csvpaths")
    return os.path.join(main.state.cwd, named_paths_rel, group_name, "group.csvpaths")


def test_do_run_warns_and_aborts_for_invalid_group(monkeypatch, qtbot, main):
    """
    do_run() must show a warning and NOT call run_paths() when group.csvpaths
    contains a match-only expression (no root '$', no scan part).
    """
    _register_hello_world(main)

    # Overwrite the group.csvpaths with an invalid match-only expression
    group_file = _group_csvpaths_path(main, "hello-world")
    assert os.path.isfile(group_file), f"Expected group.csvpaths at: {group_file}"
    with open(group_file, "w", encoding="utf-8") as fh:
        fh.write(
            "---- CSVPATH ----\n\n~\n   id: hello world\n   test-data:\n~\n"
            " print(\"hello world\") \n"
        )

    dialog = NewRunDialog(
        main=main, named_paths="hello-world", named_file="test", parent=main.sidebar
    )
    qtbot.addWidget(dialog)

    warnings = []
    monkeypatch.setattr(meut, "warning2", lambda **kwargs: warnings.append(kwargs))

    run_paths_calls = []
    monkeypatch.setattr(main, "run_paths", lambda **kwargs: run_paths_calls.append(kwargs))

    dialog.do_run()

    assert len(warnings) == 1, (
        f"Expected exactly one warning dialog; got {len(warnings)}: {warnings}"
    )
    assert len(run_paths_calls) == 0, (
        "run_paths must not be called when the named-paths group is invalid"
    )


def test_do_run_warning_mentions_group_name(monkeypatch, qtbot, main):
    """The warning message must name the offending named-paths group."""
    _register_hello_world(main)

    group_file = _group_csvpaths_path(main, "hello-world")
    with open(group_file, "w", encoding="utf-8") as fh:
        fh.write("---- CSVPATH ----\n\n print(\"bad\") \n")

    dialog = NewRunDialog(
        main=main, named_paths="hello-world", named_file="test", parent=main.sidebar
    )
    qtbot.addWidget(dialog)

    warnings = []
    monkeypatch.setattr(meut, "warning2", lambda **kwargs: warnings.append(kwargs))
    monkeypatch.setattr(main, "run_paths", lambda **kwargs: None)

    dialog.do_run()

    assert warnings, "Expected a warning"
    assert "hello-world" in warnings[0].get("msg", ""), (
        "Warning message must include the named-paths group name"
    )


def test_do_run_proceeds_with_valid_group(monkeypatch, qtbot, main):
    """do_run() must call run_paths() when group.csvpaths is valid."""
    _register_hello_world(main)

    run_paths_calls = []
    monkeypatch.setattr(main, "run_paths", lambda **kwargs: run_paths_calls.append(kwargs))

    dialog = NewRunDialog(
        main=main, named_paths="hello-world", named_file="test", parent=main.sidebar
    )
    qtbot.addWidget(dialog)

    dialog.do_run()

    assert len(run_paths_calls) == 1, (
        "run_paths must be called exactly once when the named-paths group is valid"
    )
