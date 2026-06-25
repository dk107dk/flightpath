"""
Unit tests for TemplateDialog.clean_or_reject()
(flightpath/dialogs/template_dialog.py).

The method was refactored: the old validation logic (now in a dead docstring
block) was replaced by a call to temu.validate() from csvpath.  The new
contract is:

  - Invalid templates raise ValueError (not return ("", True) as before).
  - The sole non-raising rejection is t=None → ("", True).
  - Valid templates return (t, False) with t unchanged.
  - `end` must be non-None and colon-prefixed, or ValueError is raised before
    validation even begins.

The original single-function test (19 assertions in one body) is replaced here
by one function per case so failures are individually named and isolated.

Run with:
  poetry run python -m pytest tests/test_templates.py -v
"""

import pytest

from flightpath.dialogs.template_dialog import TemplateDialog


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_END = ":run_dir"


def _ok(t: str, end: str = _END) -> tuple:
    return TemplateDialog.clean_or_reject(end=end, t=t)


def _raises(t: str, end: str = _END) -> None:
    with pytest.raises(ValueError):
        TemplateDialog.clean_or_reject(end=end, t=t)


# ---------------------------------------------------------------------------
# end parameter validation (checked before temu.validate is called)
# ---------------------------------------------------------------------------


def test_end_none_raises():
    with pytest.raises(ValueError, match="End cannot be None"):
        TemplateDialog.clean_or_reject(end=None, t="a/:run_dir")


def test_end_without_colon_prefix_raises():
    with pytest.raises(ValueError, match="End must start with :"):
        TemplateDialog.clean_or_reject(end="run_dir", t="a/:run_dir")


# ---------------------------------------------------------------------------
# t=None — the only path that returns ("", True) without raising
# ---------------------------------------------------------------------------


def test_t_none_returns_empty_true():
    """None is handled before temu.validate; returns ("", True) not ValueError."""
    assert _ok(None) == ("", True)


# ---------------------------------------------------------------------------
# Valid templates — return (t, False) with t unchanged
# ---------------------------------------------------------------------------


def test_simple_path_ending_in_run_dir():
    assert _ok("a/:run_dir") == ("a/:run_dir", False)


def test_path_with_numeric_index_token():
    assert _ok(":0/a/:run_dir") == (":0/a/:run_dir", False)


def test_path_with_prefix_and_index():
    assert _ok("b/:0/a/:run_dir") == ("b/:0/a/:run_dir", False)


def test_path_with_two_index_tokens():
    assert _ok("b/:0/:1/:run_dir") == ("b/:0/:1/:run_dir", False)


def test_path_with_two_digit_index():
    assert _ok("b/:09/a/:run_dir") == ("b/:09/a/:run_dir", False)


def test_valid_filename_mode():
    """When end=':filename', temu.validate is called with file=True.
    Avoid single-char path segments — rstrip('/:filename') strips those chars
    character-by-character, which eats short paths like 'a'."""
    assert _ok("bx/:filename", end=":filename") == ("bx/:filename", False)


def test_valid_filename_mode_longer_path():
    assert _ok("projects/my-project/:filename", end=":filename") == (
        "projects/my-project/:filename",
        False,
    )


# ---------------------------------------------------------------------------
# Invalid — wrong or missing end marker
# ---------------------------------------------------------------------------


def test_empty_string_raises():
    _raises("")


def test_single_slash_raises():
    _raises("/")


def test_backslash_raises():
    _raises("\\")


def test_colon_prefix_non_run_dir_raises():
    _raises(":a")


def test_double_slash_raises():
    _raises("//")


def test_url_raises():
    """A URL-like string does not end with :run_dir."""
    _raises("http://abc")


def test_windows_path_with_drive_letter_raises():
    _raises("c:\\abc")


def test_path_ending_without_run_dir_raises():
    _raises("a/b/c")


def test_path_run_dir_not_at_end_raises():
    """:run_dir must be the final component, not a middle segment."""
    _raises(":run_dir/c")


# ---------------------------------------------------------------------------
# Invalid — starts with slash or end marker
# ---------------------------------------------------------------------------


def test_leading_slash_raises():
    """:run_dir must not be preceded by a leading slash on the whole path."""
    _raises("/:run_dir")


def test_leading_slash_with_content_raises():
    _raises("/b/:09/a/:run_dir")


def test_starts_with_end_marker_raises():
    _raises(":run_dir")


def test_end_marker_appears_twice_raises():
    """:run_dir cannot appear as the first segment even if it recurs later."""
    _raises(":run_dir/c/:run_dir")


# ---------------------------------------------------------------------------
# Invalid — illegal characters and colon token rules
# ---------------------------------------------------------------------------


def test_non_numeric_colon_token_raises():
    """Colon-led tokens in the path must be digits (:0, :09, …), not letters."""
    _raises("a/:b/:run_dir")


def test_dot_character_raises():
    """Dot is in the illegal-character list."""
    _raises("a/b.c/:run_dir")


def test_question_mark_raises():
    _raises("a/b?/:run_dir")


def test_bracket_raises():
    _raises("a/b[c]/:run_dir")
