"""
Unit tests for ExamplesMarshal.add_examples()
(flightpath/util/examples_marshal.py).

add_examples() reads list.txt from source_path, then copies each listed file
into path/.  Comment lines (starting with '#') and blank lines are skipped.

The original test created and destroyed tests/test_resources/examples/ —
shared state that could cause failures on concurrent or repeated runs.
This rewrite uses tmp_path so the output directory is fresh and isolated for
every test.

Run with:
  poetry run python -m pytest tests/test_examples.py -v
"""

import os

import pytest

from flightpath.util.examples_marshal import ExamplesMarshal

SOURCE = os.path.join("tests", "test_resources", "examples_source")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _run(tmp_path):
    em = ExamplesMarshal(None)
    em.add_examples(path=str(tmp_path), source_path=SOURCE)
    return sorted(os.listdir(tmp_path))


# ---------------------------------------------------------------------------
# File count and names
# ---------------------------------------------------------------------------


def test_add_examples_copies_expected_file_count(tmp_path):
    """list.txt lists two files (comment line is skipped); both must be copied."""
    files = _run(tmp_path)
    assert len(files) == 2


def test_add_examples_copies_csv_file(tmp_path):
    files = _run(tmp_path)
    assert "test.csv" in files


def test_add_examples_copies_csvpath_file(tmp_path):
    files = _run(tmp_path)
    assert "test.csvpath" in files


# ---------------------------------------------------------------------------
# File content
# ---------------------------------------------------------------------------


def test_copied_csv_is_non_empty(tmp_path):
    """The copied CSV must have content — not an empty file."""
    _run(tmp_path)
    content = (tmp_path / "test.csv").read_text()
    assert len(content.strip()) > 0


def test_copied_csvpath_is_non_empty(tmp_path):
    """The copied csvpath file must have content — not an empty file."""
    _run(tmp_path)
    content = (tmp_path / "test.csvpath").read_text()
    assert len(content.strip()) > 0


def test_copied_csv_matches_source(tmp_path):
    """The copied file must be byte-for-byte identical to the source file."""
    _run(tmp_path)
    src = os.path.join(SOURCE, "test.csv")
    assert (tmp_path / "test.csv").read_text() == open(src).read()


# ---------------------------------------------------------------------------
# Source directory is not modified
# ---------------------------------------------------------------------------


def test_source_directory_unchanged_after_copy(tmp_path):
    """add_examples must not add or remove files from source_path."""
    before = sorted(os.listdir(SOURCE))
    _run(tmp_path)
    after = sorted(os.listdir(SOURCE))
    assert before == after


# ---------------------------------------------------------------------------
# Output directory starts empty
# ---------------------------------------------------------------------------


def test_output_dir_empty_before_run(tmp_path):
    """Sanity check: tmp_path is empty before we run add_examples."""
    assert os.listdir(tmp_path) == []


def test_output_dir_populated_after_run(tmp_path):
    files = _run(tmp_path)
    assert len(files) > 0
