"""
Unit tests for JsonUtility (flightpath/util/json_utility.py).

Covers:
  is_jsonl — returns True for .jsonl, .jsonlines, and paths ending with "ndjson"

Notable quirk: the third check is path.endswith("ndjson") with no leading dot,
so any path whose final characters are "ndjson" matches — including
"data_ndjson" or even bare "ndjson".  This is pinned here so a tighter fix
is noticed.

Run with:
  poetry run python -m pytest tests/test_json_utility.py -v
"""

import pytest

from flightpath.util.json_utility import JsonUtility as jsut


# ---------------------------------------------------------------------------
# is_jsonl — matching extensions
# ---------------------------------------------------------------------------


def test_is_jsonl_dotjsonl_returns_true():
    assert jsut.is_jsonl("data.jsonl") is True


def test_is_jsonl_dotjsonlines_returns_true():
    assert jsut.is_jsonl("data.jsonlines") is True


def test_is_jsonl_dotndjson_returns_true():
    """'.ndjson' ends with 'ndjson' (no leading dot in the check) → True."""
    assert jsut.is_jsonl("data.ndjson") is True


def test_is_jsonl_path_with_directories():
    assert jsut.is_jsonl("/some/dir/records.jsonl") is True


# ---------------------------------------------------------------------------
# is_jsonl — non-matching extensions
# ---------------------------------------------------------------------------


def test_is_jsonl_dotjson_returns_false():
    """.json is NOT .jsonl — must not be matched."""
    assert jsut.is_jsonl("data.json") is False


def test_is_jsonl_dotcsv_returns_false():
    assert jsut.is_jsonl("data.csv") is False


def test_is_jsonl_empty_string_returns_false():
    assert jsut.is_jsonl("") is False


def test_is_jsonl_case_sensitive():
    """The check is case-sensitive: .JSONL does not match .jsonl."""
    assert jsut.is_jsonl("data.JSONL") is False


# ---------------------------------------------------------------------------
# is_jsonl — notable quirk: no dot required before "ndjson"
# ---------------------------------------------------------------------------


def test_is_jsonl_no_dot_ndjson_suffix_returns_true():
    """
    The source uses path.endswith("ndjson") without a leading dot, so any
    path ending in the bare characters "ndjson" matches — including
    non-standard filenames like "my_ndjson".  This test pins the current
    behaviour; a dot-prefixed check would be the correct fix.
    """
    assert jsut.is_jsonl("my_ndjson") is True


# ---------------------------------------------------------------------------
# is_jsonl — None guard (missing)
# ---------------------------------------------------------------------------


def test_is_jsonl_none_raises_attribute_error():
    """
    is_jsonl has no None guard; None.endswith() raises AttributeError.
    This test documents the current behaviour.
    """
    with pytest.raises(AttributeError):
        jsut.is_jsonl(None)
