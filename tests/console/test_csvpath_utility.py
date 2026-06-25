"""
Unit tests for CsvpathUtility (flightpath/util/csvpath_utility.py).

_add_to_external_comment_of_csvpath_at_position is already covered in
tests/test_insert_metadata.py.  This file covers the remaining methods:

  _get_char             — maps char names to their actual characters
  get_filepath          — extracts test-data path from an external comment
  get_delimiter         — extracts test-delimiter from an external comment
  get_quotechar         — extracts test-quotechar from an external comment
  statement_and_comment — splits a csvpath string into statement + comment

IMPORTANT — comment format for get_filepath / get_delimiter / get_quotechar:
  These methods receive the INNER comment text, i.e. what statement_and_comment
  returns as its second element — the content between the ~ markers, stripped
  of the markers themselves.  Passing a raw string that still includes ~ will
  cause MetadataParser to include the trailing ~ in the extracted value.

Known bugs pinned here:

1. _get_char("tab", default): returns "" instead of "\t" because the final
   c.strip() call strips the tab character.

2. _get_char("int", default): when exut.to_int("int") fails the except branch
   is `...` (no assignment), so c remains "int" and is returned unchanged
   instead of falling back to the default.

3. get_delimiter(None) and get_quotechar(None): unlike get_filepath which
   guards against None at the top, these methods pass None directly to
   get_metadata() → MetadataParser._collect_metadata() → TypeError when it
   iterates over None.

Run with:
  poetry run python -m pytest tests/test_csvpath_utility.py -v
"""

import pytest

from flightpath.util.csvpath_utility import CsvpathUtility as cput

# ---------------------------------------------------------------------------
# Shared test strings
# A csvpath string with an external comment.  The outer ~ markers are part
# of the csvpath syntax; statement_and_comment strips them and returns the
# inner text as the comment.
# ---------------------------------------------------------------------------

_BARE_CSVPATH = "$[*][yes()]"
_OUTER_COMMENT_TEXT = "test-data: /data/test.csv"
_FULL_CSVPATH = f"~ {_OUTER_COMMENT_TEXT} ~\n{_BARE_CSVPATH}"

# Outer comment text (no ~ markers) — the format get_filepath/get_delimiter/
# get_quotechar expect as input.


# ---------------------------------------------------------------------------
# _get_char — char name → actual character
# ---------------------------------------------------------------------------


def test_get_char_pipe():
    assert cput._get_char("pipe", ",") == "|"


def test_get_char_bar_alias():
    assert cput._get_char("bar", ",") == "|"


def test_get_char_comma():
    assert cput._get_char("comma", "|") == ","


def test_get_char_semicolon():
    assert cput._get_char("semicolon", ",") == ";"


def test_get_char_semi_colon_hyphenated():
    assert cput._get_char("semi-colon", ",") == ";"


@pytest.mark.xfail(strict=True, reason="Bug: c.strip() strips the tab character to ''")
def test_get_char_tab_returns_tab_character():
    """c.strip() strips the tab; fix is to return '\\t' before the strip call."""
    assert cput._get_char("tab", ",") == "\t"


def test_get_char_quotes():
    assert cput._get_char("quotes", "'") == '"'


def test_get_char_single_quote():
    assert cput._get_char("single-quote", '"') == "'"


def test_get_char_singlequote_no_hyphen():
    assert cput._get_char("singlequote", '"') == "'"


def test_get_char_unknown_name_returns_default():
    """A name not in CHAR_NAMES falls through to the default."""
    assert cput._get_char("not_a_real_name", ",") == ","


@pytest.mark.xfail(strict=True, reason="Bug: except branch is bare '...' so c stays 'int' instead of falling back to default")
def test_get_char_non_numeric_name_falls_back_to_default():
    """When to_int() fails the except branch should set c = None to trigger the default."""
    assert cput._get_char("int", ",") == ","


def test_get_char_at_sign():
    assert cput._get_char("at", ",") == "@"


def test_get_char_hash():
    assert cput._get_char("hash", ",") == "#"


# ---------------------------------------------------------------------------
# get_filepath — expects inner comment text (no ~ markers)
# ---------------------------------------------------------------------------


def test_get_filepath_extracts_path_from_comment():
    """Pass the comment (no ~ markers) — the format used in production."""
    result = cput.get_filepath("test-data: /data/test.csv")
    assert result == "/data/test.csv"


def test_get_filepath_via_statement_and_comment():
    """The canonical use: extract comment first, then call get_filepath."""
    _, comment = cput.statement_and_comment(_FULL_CSVPATH)
    result = cput.get_filepath(comment)
    assert result == "/data/test.csv"


def test_get_filepath_with_raw_tilde_markers_includes_trailing_marker():
    """
    Passing the raw string including ~ markers is the wrong input format.
    The trailing ' ~' is included in the extracted value.  Pin this to
    document that callers must strip ~ markers first.
    """
    result = cput.get_filepath("~ test-data: /data/test.csv ~")
    assert result is not None
    assert "~" in result, "trailing ~ is included when markers are not stripped"


def test_get_filepath_no_annotation_returns_none():
    assert cput.get_filepath("some other metadata: value") is None


def test_get_filepath_empty_comment_returns_none():
    assert cput.get_filepath("") is None


def test_get_filepath_none_comment_returns_none():
    assert cput.get_filepath(None) is None


def test_get_filepath_path_with_newline_truncated_at_newline():
    result = cput.get_filepath("test-data: /data/test.csv\nextra")
    assert "\n" not in result
    assert result == "/data/test.csv"


# ---------------------------------------------------------------------------
# statement_and_comment
# ---------------------------------------------------------------------------


def test_statement_and_comment_returns_tuple():
    result = cput.statement_and_comment(_FULL_CSVPATH)
    assert isinstance(result, tuple) and len(result) == 2


def test_statement_and_comment_extracts_statement():
    statement, _ = cput.statement_and_comment(_FULL_CSVPATH)
    assert _BARE_CSVPATH in statement


def test_statement_and_comment_extracts_inner_comment():
    _, comment = cput.statement_and_comment(_FULL_CSVPATH)
    assert "test-data" in comment
    assert "~" not in comment


def test_statement_and_comment_both_parts_are_stripped():
    padded = f"  {_FULL_CSVPATH}  "
    statement, comment = cput.statement_and_comment(padded)
    assert not statement.startswith(" ")
    assert not comment.endswith(" ")


def test_statement_and_comment_no_comment_returns_empty_comment():
    statement, comment = cput.statement_and_comment(_BARE_CSVPATH)
    assert _BARE_CSVPATH in statement
    assert comment == ""


# ---------------------------------------------------------------------------
# get_delimiter — expects comment text
# ---------------------------------------------------------------------------


def test_get_delimiter_pipe():
    """Pass the comment (no ~ markers)."""
    assert cput.get_delimiter("test-delimiter: pipe") == "|"


@pytest.mark.xfail(strict=True, reason="Bug: same c.strip() bug strips tab to '' in _get_char")
def test_get_delimiter_tab_returns_tab_character():
    assert cput.get_delimiter("test-delimiter: tab") == "\t"


def test_get_delimiter_no_annotation_returns_none():
    assert cput.get_delimiter("no delimiter here") is None


@pytest.mark.xfail(strict=True, reason="Bug: missing None guard — passes None to get_metadata() which raises TypeError")
def test_get_delimiter_none_returns_none():
    assert cput.get_delimiter(None) is None


# ---------------------------------------------------------------------------
# get_quotechar — expects inner comment text
# ---------------------------------------------------------------------------


def test_get_quotechar_double_quote():
    assert cput.get_quotechar("test-quotechar: quotes") == '"'


def test_get_quotechar_single_quote():
    assert cput.get_quotechar("test-quotechar: single-quote") == "'"


def test_get_quotechar_no_annotation_returns_none():
    assert cput.get_quotechar("some comment") is None


@pytest.mark.xfail(strict=True, reason="Bug: missing None guard — same as get_delimiter")
def test_get_quotechar_none_returns_none():
    assert cput.get_quotechar(None) is None
