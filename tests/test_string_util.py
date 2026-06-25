"""
Unit tests for StringUtility (flightpath/util/string_utility.py).

Covers:
  jsonl_text_to_list  — parse concatenated JSON objects/lines from raw text
  jsonl_text_to_lines — same parsing, returned as a newline-joined string
  good_name           — character allowlist validator for project/file names
  sanitize_json       — strip literal control characters from a JSON string

Run with:
  poetry run python -m pytest tests/test_string_util.py -v
"""

import pytest

from flightpath.util.string_utility import StringUtility as strut


# ---------------------------------------------------------------------------
# jsonl_text_to_list
# ---------------------------------------------------------------------------


def test_jsonl_text_to_list_two_objects():
    """Two concatenated JSON objects (with whitespace between) return a 2-item list."""
    text = """
        { "a":"b"}{
        "c":
        "d"
        }
    """
    result = strut.jsonl_text_to_list(text)
    assert len(result) == 2


def test_jsonl_text_to_list_single_object():
    """A single JSON object returns a 1-item list."""
    result = strut.jsonl_text_to_list('{"key": "value"}')
    assert len(result) == 1
    assert '"key"' in result[0]


def test_jsonl_text_to_list_empty_string_returns_empty_list():
    """An empty string produces an empty list (no items to parse)."""
    result = strut.jsonl_text_to_list("")
    assert result == []


def test_jsonl_text_to_list_whitespace_only_returns_empty_list():
    """A whitespace-only string (spaces, tabs, newlines) produces an empty list."""
    result = strut.jsonl_text_to_list("   \t\n   ")
    assert result == []


def test_jsonl_text_to_list_none_returns_empty_string():
    """
    None input returns "" (an empty string, not a list).  This is the current
    contract; callers that need a list must guard against None upstream.
    """
    result = strut.jsonl_text_to_list(None)
    assert result == ""


def test_jsonl_text_to_list_malformed_json_returned_as_raw_string():
    """
    Malformed JSON that never closes a valid object accumulates in the internal
    buffer and is returned as a raw string entry rather than raising.  The parser
    is lenient by design.
    """
    result = strut.jsonl_text_to_list('{"key": "unclosed string}')
    assert len(result) == 1


def test_jsonl_text_to_list_valid_followed_by_trailing_garbage():
    """A valid object followed by trailing text returns both: the parsed object
    and the leftover text as a second entry."""
    result = strut.jsonl_text_to_list('{"a":"b"}trailing')
    assert len(result) == 2
    assert any('"a"' in r for r in result)


# ---------------------------------------------------------------------------
# good_name — default allowlist
# ---------------------------------------------------------------------------


def test_good_name_valid_alphanumeric_and_default_extras():
    """Letters, digits, space, dash, and underscore are all accepted by default."""
    assert strut.good_name("abc DEF - 123_") is True


def test_good_name_semicolon_rejected_by_default():
    """Semicolons and question marks are not in the default allowlist."""
    assert strut.good_name("abc; DEF?= - 123_") is False


def test_good_name_none_returns_false():
    assert strut.good_name(None) is False


def test_good_name_empty_string_returns_false():
    assert strut.good_name("") is False


def test_good_name_whitespace_only_returns_false():
    assert strut.good_name("   ") is False


def test_good_name_digits_boundary_zero_and_nine():
    """'0' (chr 48) and '9' (chr 57) are the digit boundaries; both accepted."""
    assert strut.good_name("0") is True
    assert strut.good_name("9") is True


def test_good_name_colon_accepted_by_default():
    """
    The digit range is range(48, 59), which includes chr(58) = ':'.
    Colon is therefore in the default allowlist — a non-obvious quirk worth
    pinning so that if the range is ever tightened this test flags the change.
    """
    assert strut.good_name(":") is True


def test_good_name_slash_and_semicolon_outside_digit_range():
    """'/' (chr 47) and ';' (chr 59) lie just outside the digit range and are rejected."""
    assert strut.good_name("/") is False
    assert strut.good_name(";") is False


def test_good_name_uppercase_boundary_a_and_z():
    """'A' (chr 65) and 'Z' (chr 90) are the uppercase boundaries; both accepted."""
    assert strut.good_name("A") is True
    assert strut.good_name("Z") is True


def test_good_name_chars_outside_uppercase_range_rejected():
    """'@' (chr 64) and '[' (chr 91) lie just outside the uppercase range."""
    assert strut.good_name("@") is False
    assert strut.good_name("[") is False


def test_good_name_lowercase_boundary_a_and_z():
    """'a' (chr 97) and 'z' (chr 122) are the lowercase boundaries; both accepted."""
    assert strut.good_name("a") is True
    assert strut.good_name("z") is True


def test_good_name_chars_outside_lowercase_range_rejected():
    """'`' (chr 96) and '{' (chr 123) lie just outside the lowercase range."""
    assert strut.good_name("`") is False
    assert strut.good_name("{") is False


def test_good_name_default_extra_chars_accepted():
    """Space (chr 32), dash (chr 45), and underscore (chr 95) are in the defaults.
    Space-only is rejected by the strip() guard, so it must appear in a longer name."""
    assert strut.good_name("a b") is True
    assert strut.good_name("a-b") is True
    assert strut.good_name("a_b") is True


def test_good_name_chars_adjacent_to_default_extras_rejected():
    """Characters just outside the default extras are not accepted without custom chars."""
    assert strut.good_name("!") is False   # chr 33, just above space
    assert strut.good_name(",") is False   # chr 44, just below dash
    assert strut.good_name(".") is False   # chr 46, just above dash
    assert strut.good_name("^") is False   # chr 94, just below underscore
    assert strut.good_name("`") is False   # chr 96, just above underscore


# ---------------------------------------------------------------------------
# good_name — custom chars parameter
# ---------------------------------------------------------------------------


def test_good_name_custom_chars_expand_allowlist():
    """When custom chars are provided, those characters are accepted in addition
    to the alphanumeric base set."""
    assert strut.good_name("abc; DEF?= - 123_", "?= -_;") is True


def test_good_name_custom_chars_replace_default_extras():
    """
    When custom chars are provided, the defaults (space, dash, underscore) are
    NOT automatically included — only the alphanumeric base and the explicit
    custom chars.  A name with a dash fails if dash is not in custom chars.
    """
    assert strut.good_name("abc-def", "?;") is False


def test_good_name_custom_chars_includes_dash_explicitly():
    """If dash is needed, it must appear in the custom chars string."""
    assert strut.good_name("abc-def", "-") is True


# ---------------------------------------------------------------------------
# sanitize_json
# ---------------------------------------------------------------------------


def test_sanitize_json_removes_control_characters():
    """Control characters (chr 0–31) must be stripped from the text."""
    text_with_ctrl = "hello\x00\x01\x1fworld"
    result = strut.sanitize_json(text_with_ctrl)
    assert result == "helloworld"


def test_sanitize_json_preserves_printable_ascii():
    """Normal printable text must pass through unchanged."""
    text = '{"key": "value", "n": 42}'
    assert strut.sanitize_json(text) == text


def test_sanitize_json_preserves_space():
    """Space (chr 32) is at the boundary and must NOT be stripped."""
    assert strut.sanitize_json("a b") == "a b"


def test_sanitize_json_empty_string():
    """An empty string returns an empty string without raising."""
    assert strut.sanitize_json("") == ""


# ---------------------------------------------------------------------------
# jsonl_text_to_lines — newline-joined variant
# ---------------------------------------------------------------------------


def test_jsonl_text_to_lines_returns_string():
    """jsonl_text_to_lines returns a str, not a list — despite the type hint."""
    result = strut.jsonl_text_to_lines('{"a":1}')
    assert isinstance(result, str)


def test_jsonl_text_to_lines_single_object_no_newline():
    """A single parsed object produces a string with no newline."""
    result = strut.jsonl_text_to_lines('{"a":1}')
    assert "\n" not in result


def test_jsonl_text_to_lines_two_objects_joined_with_newline():
    """Two objects are joined with a single newline between them."""
    result = strut.jsonl_text_to_lines('{"a":1}\n{"b":2}')
    parts = result.split("\n")
    assert len(parts) == 2


def test_jsonl_text_to_lines_empty_string_returns_empty():
    assert strut.jsonl_text_to_lines("") == ""
