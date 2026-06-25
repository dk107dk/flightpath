"""
Unit tests for TDataUtility.test_data_path_from_csvpath()
(flightpath/util/tdata_utility.py).

TDataUtility.MARKER == '---- CSVPATH ----' (from PathsManager).  This marker
separates multiple csvpath definitions in a .csvpaths file.  Within each
block, the ~...~ notation is csvpath's own comment syntax, processed by
MetadataParser.  test-data: annotations live inside those comments.

Run with:
  poetry run python -m pytest tests/test_test_data_utility.py -v
"""

import pytest

from flightpath.util.tdata_utility import TDataUtility as tdut

# Convenience alias so test bodies can reference the separator clearly.
MARKER = tdut.MARKER


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------


def test_returns_path_from_test_data_annotation():
    """Standard single-csvpath text with a test-data annotation."""
    text = """
        ~ test-data:a/b/c.csv ~
        $[*][ yes()]
    """
    assert tdut.test_data_path_from_csvpath(text) == "a/b/c.csv"


# ---------------------------------------------------------------------------
# No annotation present
# ---------------------------------------------------------------------------


def test_no_test_data_annotation_returns_none():
    """A csvpath comment that contains no test-data: key returns None."""
    text = "~ some other comment ~\n$[*][ yes()]"
    assert tdut.test_data_path_from_csvpath(text) is None


def test_no_comment_block_at_all_returns_none():
    """Plain csvpath text with no ~ comment block and no test-data: returns None."""
    text = "$[*][ yes()]"
    assert tdut.test_data_path_from_csvpath(text) is None


def test_empty_string_returns_none():
    """An empty string produces no blocks to search and returns None."""
    assert tdut.test_data_path_from_csvpath("") is None


# ---------------------------------------------------------------------------
# Multiple csvpath definitions (MARKER-separated)
# ---------------------------------------------------------------------------


def test_multiple_csvpaths_returns_first_annotation():
    """
    When several csvpath definitions are separated by MARKER, the method
    returns the test-data path from the FIRST block that contains one.
    The loop breaks immediately after the first match.
    """
    text = (
        f"~ test-data:first.csv ~\n$[*][ yes()]\n"
        f"{MARKER}\n"
        f"~ test-data:second.csv ~\n$[*][ no()]"
    )
    assert tdut.test_data_path_from_csvpath(text) == "first.csv"


def test_annotation_in_second_block_when_first_has_none():
    """When the first block has no test-data: annotation, the second block
    is searched and its path is returned."""
    text = (
        f"~ no annotation here ~\n$[*][ yes()]\n"
        f"{MARKER}\n"
        f"~ test-data:found.csv ~\n$[*][ no()]"
    )
    assert tdut.test_data_path_from_csvpath(text) == "found.csv"


# ---------------------------------------------------------------------------
# Whitespace handling
# ---------------------------------------------------------------------------


def test_leading_and_trailing_whitespace_around_path_stripped():
    """get_filepath() calls filepath.strip() so surrounding spaces are removed."""
    text = "~ test-data:  a/b/c.csv  ~\n$[*][ yes()]"
    assert tdut.test_data_path_from_csvpath(text) == "a/b/c.csv"


# ---------------------------------------------------------------------------
# Malformed / edge-case annotations
# ---------------------------------------------------------------------------


def test_colon_with_no_path_returns_none():
    """test-data: with no value after the colon produces None (MetadataParser
    returns None for an empty value, not an empty string)."""
    text = "~ test-data: ~\n$[*][ yes()]"
    assert tdut.test_data_path_from_csvpath(text) is None


# ---------------------------------------------------------------------------
# None input — documents missing guard
# ---------------------------------------------------------------------------


def test_none_input_raises():
    """
    test_data_path_from_csvpath has no None guard: calling csvpath.split()
    on None raises AttributeError.  This test pins the current (unguarded)
    behavior so that if a guard is added later, the test is updated too.
    """
    with pytest.raises((AttributeError, TypeError)):
        tdut.test_data_path_from_csvpath(None)
