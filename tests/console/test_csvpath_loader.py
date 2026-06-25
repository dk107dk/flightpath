"""
Unit tests for CsvpathLoader._do_load_file error messaging
(flightpath/actions/csvpath_loader.py).

These tests verify that when add_named_paths_from_file returns None the
warning shown to the user includes the filename and actionable guidance
rather than the previously unhelpful 'Cannot load file' string.

Run with:
  poetry run python -m pytest tests/console/test_csvpath_loader.py -v
"""

import os
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from flightpath.actions.csvpath_loader import CsvpathLoader


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_loader(tmp_path, add_named_paths_return=None):
    """
    Build a CsvpathLoader wired to lightweight stubs.

    load_dialog.path points at a real .csvpath file in tmp_path so that
    Nos(name).isfile() returns True and the extension check passes.
    """
    csvpath_file = tmp_path / "bad_match_only.csvpath"
    csvpath_file.write_text(" not(all()) -> counter.lines_with_blanks() ")

    # Stub for load_dialog
    warning_calls = []

    class _FakeDialog:
        path = str(csvpath_file)
        template_ctl = None
        named_paths_name_ctl = None

        def warning(self, *, msg, title):
            warning_calls.append({"msg": msg, "title": title})

        def yesNo(self, **kwargs):
            pass

    # Stub for paths_manager
    paths_manager = MagicMock()
    paths_manager.has_named_paths.return_value = False
    paths_manager.add_named_paths_from_file.return_value = add_named_paths_return

    # Stub for csvpaths
    csvpaths = MagicMock()
    csvpaths.paths_manager = paths_manager

    # Stub for csvpath_config — must accept keyword args matching the real call
    def _config_get(*, section, name):
        if section == "extensions" and name == "csvpath_files":
            return ["csvpath", "csvpaths"]
        return []

    csvpath_config = SimpleNamespace(get=_config_get)

    # Stub for main
    main = SimpleNamespace(
        csvpaths=csvpaths,
        csvpath_config=csvpath_config,
        sidebar=MagicMock(),
        welcome=MagicMock(),
    )
    main.sidebar._renew_sidebars = MagicMock()
    main.welcome.update_run_button = MagicMock()

    loader = CsvpathLoader(main=main, parent=MagicMock())
    loader.load_dialog = _FakeDialog()

    return loader, warning_calls


# ---------------------------------------------------------------------------
# Tests: do_load_file → _do_load_file → warning when ref is None
# ---------------------------------------------------------------------------


def test_load_failure_warning_includes_filename(tmp_path):
    """The warning message must name the file that failed to load."""
    loader, calls = _make_loader(tmp_path, add_named_paths_return=None)

    loader.do_load_file(overwrite=True)

    assert len(calls) == 1
    assert "bad_match_only.csvpath" in calls[0]["msg"]


def test_load_failure_warning_title_is_cannot_load(tmp_path):
    """The warning title must be 'Cannot Load'."""
    loader, calls = _make_loader(tmp_path, add_named_paths_return=None)

    loader.do_load_file(overwrite=True)

    assert calls[0]["title"] == "Cannot Load"


def test_load_failure_warning_mentions_scan_and_match(tmp_path):
    """The warning must tell the user that both scan and match sections are required."""
    loader, calls = _make_loader(tmp_path, add_named_paths_return=None)

    loader.do_load_file(overwrite=True)

    msg = calls[0]["msg"].lower()
    assert "scan" in msg and "match" in msg, (
        "Warning must mention both scan and match sections to guide the user"
    )


def test_load_success_shows_no_warning(tmp_path):
    """When loading succeeds (ref is not None) no warning must be shown."""
    loader, calls = _make_loader(tmp_path, add_named_paths_return="my_group")

    loader.do_load_file(overwrite=True)

    assert len(calls) == 0, "No warning expected on successful load"


def test_load_failure_empty_ref_shows_warning(tmp_path):
    """A blank-string ref (not None) must also trigger the warning."""
    loader, calls = _make_loader(tmp_path, add_named_paths_return="   ")

    loader.do_load_file(overwrite=True)

    assert len(calls) == 1
