"""
Unit tests for CsvPathTextEdit._add_to_external_comment_of_csvpath_at_position()
(flightpath/widgets/csvpath_text_edit.py → delegates to CsvpathUtility).

The method locates the csvpath block that contains `position`, prepends `addto`
to the leading external comment of that block, and returns the modified full
text together with a debug dict of the sub-parts.

Input shapes covered:
  ONE   — single csvpath, tight comment (no spaces inside ~)
  TWO   — single csvpath, spaced comment
  THREE — single csvpath preceded by a MARKER separator
  FOUR  — three csvpaths separated by two MARKERs; position selects the middle block

Run with:
  poetry run python -m pytest tests/test_insert_metadata.py -v
"""

import pytest

from flightpath.widgets.csvpath_text_edit import CsvPathTextEdit

# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

ONE   = " ~two fish~$[*][yes()]"
TWO   = " ~ two fish ~ $[*][ yes()]"
THREE = " ---- CSVPATH ---- ~ two fish ~ $[*][ yes()] "
FOUR  = (
    " $[*][ yes()] ---- CSVPATH ---- ~ two fish ~ $[*][ yes()]"
    " ---- CSVPATH ---- ~ three bugs ~ $[*][ yes() ] "
)


def _insert(text: str, position: int, addto: str) -> str:
    """Call the method and return only the modified text string."""
    result, _ = CsvPathTextEdit._add_to_external_comment_of_csvpath_at_position(
        text=text, position=position, addto=addto
    )
    return result


# ---------------------------------------------------------------------------
# Existing four cases — one function each
# ---------------------------------------------------------------------------


def test_single_csvpath_tight_comment():
    """ONE: comment has no surrounding spaces; addto is prepended directly."""
    result = _insert(ONE, position=20, addto="add me")
    assert result.strip() == "~add metwo fish~$[*][yes()]"


def test_single_csvpath_spaced_comment():
    """TWO: comment has surrounding spaces; addto is prepended before the space."""
    result = _insert(TWO, position=20, addto="add me")
    assert result.strip() == "~add me two fish ~ $[*][ yes()]"


def test_single_csvpath_with_marker_prefix():
    """THREE: a MARKER precedes the block; addto targets the comment in that block."""
    result = _insert(THREE, position=28, addto="add me")
    assert result.strip() == "---- CSVPATH ---- ~add me two fish ~ $[*][ yes()]"


def test_multi_csvpath_targets_correct_block():
    """FOUR: position falls inside the middle block; only its comment is modified."""
    result = _insert(FOUR, position=50, addto="add me")
    assert result.strip() == (
        "$[*][ yes()] ---- CSVPATH ---- ~add me two fish ~ $[*][ yes()]"
        " ---- CSVPATH ---- ~ three bugs ~ $[*][ yes() ]"
    )


# ---------------------------------------------------------------------------
# position bounds
# ---------------------------------------------------------------------------


def test_position_at_len_raises():
    """position == len(text) is out of range; ValueError is raised."""
    with pytest.raises(ValueError, match="out of string"):
        _insert(ONE, position=len(ONE), addto="x")


def test_position_past_end_raises():
    """Any position beyond the last character raises ValueError."""
    with pytest.raises(ValueError, match="out of string"):
        _insert(ONE, position=9999, addto="x")


# ---------------------------------------------------------------------------
# addto edge cases
# ---------------------------------------------------------------------------


def test_empty_addto_leaves_comment_text_intact():
    """An empty addto string prepends nothing; the comment content is unchanged."""
    result = _insert(ONE, position=20, addto="")
    assert result.strip() == "~two fish~$[*][yes()]"


def test_empty_addto_spaced_comment_intact():
    result = _insert(TWO, position=20, addto="")
    assert result.strip() == "~ two fish ~ $[*][ yes()]"


def test_none_addto_inserts_literal_none_string():
    """
    There is no None guard on addto: Python's f-string interpolation converts
    None to the string 'None' and inserts it into the comment.  This test
    pins that (unguarded) behavior so a future fix is noticed here.
    """
    result = _insert(ONE, position=20, addto=None)
    assert "None" in result


# ---------------------------------------------------------------------------
# Text with no comment markers
# ---------------------------------------------------------------------------


def test_no_tilde_markers_creates_synthetic_comment():
    """
    When the block at `position` has no ~ comment markers, the method
    synthesizes a minimal comment by treating s='~' and comment='~',
    producing ~{addto}~{rest-of-block}.
    """
    text = "$[*][yes()]"
    result = _insert(text, position=5, addto="add me")
    assert result.strip() == "~add me~$[*][yes()]"
