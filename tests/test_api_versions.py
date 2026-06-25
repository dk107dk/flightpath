"""
Unit tests for api_util._parse_versions() and api_util.connect().

The source raises ValueError (not ApiException) for malformed version strings,
and ModuleNotFoundError (not ApiException) when no matching implementation is
found.  Two of the original four tests were testing against ApiException and
were already failing; this rewrite corrects them to match the actual contracts.

Run with:
  poetry run python -m pytest tests/test_api_versions.py -v
"""

import pytest

from flightpath.util.api import api_util as aput
from flightpath.util.api.v1 import FlightPathServerApiV1
from flightpath.util.api.v2 import FlightPathServerApiV2


# ---------------------------------------------------------------------------
# _parse_versions — format validation and descending sort
# ---------------------------------------------------------------------------


def test_parse_versions_two_versions_sorted_descending():
    assert aput._parse_versions(["v1", "v2"]) == [2, 1]


def test_parse_versions_five_versions_sorted_descending():
    result = aput._parse_versions(["v15", "v2", "v1", "v0", "v10"])
    assert result == [15, 10, 2, 1, 0]


def test_parse_versions_single_version():
    assert aput._parse_versions(["v1"]) == [1]


def test_parse_versions_v0_accepted():
    """v0 is a valid version string (single digit, v-prefixed)."""
    assert aput._parse_versions(["v0"]) == [0]


def test_parse_versions_none_raises_value_error():
    with pytest.raises(ValueError, match="cannot be None"):
        aput._parse_versions(None)


def test_parse_versions_empty_list_raises_value_error():
    with pytest.raises(ValueError, match="not provided"):
        aput._parse_versions([])


def test_parse_versions_float_version_raises_value_error():
    """'v1.5' does not match r'v(\\d+)' — floats are rejected."""
    with pytest.raises(ValueError, match="Unrecognized version format"):
        aput._parse_versions(["v1.5", "v2", "v1", "v0"])


def test_parse_versions_no_v_prefix_raises_value_error():
    """A bare integer without the 'v' prefix is rejected."""
    with pytest.raises(ValueError, match="Unrecognized version format"):
        aput._parse_versions(["1"])


def test_parse_versions_word_raises_value_error():
    """An arbitrary word like 'latest' is rejected."""
    with pytest.raises(ValueError, match="Unrecognized version format"):
        aput._parse_versions(["latest"])


def test_parse_versions_mixed_valid_and_invalid_raises():
    """A mix of valid and invalid versions raises on the first bad entry."""
    with pytest.raises(ValueError):
        aput._parse_versions(["v1", "v2", "bad"])


# ---------------------------------------------------------------------------
# connect — version factory with fallback
# ---------------------------------------------------------------------------


def test_connect_v1_returns_v1_instance():
    api = aput.connect("http://localhost:8000", ["v1"])
    assert isinstance(api, FlightPathServerApiV1)


def test_connect_v2_returns_v2_instance():
    api = aput.connect("http://localhost:8000", ["v2"])
    assert isinstance(api, FlightPathServerApiV2)


def test_connect_prefers_highest_version():
    """When both v1 and v2 are offered, connect returns the v2 implementation."""
    api = aput.connect("http://localhost:8000", ["v1", "v2"])
    assert isinstance(api, FlightPathServerApiV2)


def test_connect_falls_back_to_lower_version():
    """When the highest offered version has no local implementation, connect
    falls back to the next highest that does."""
    api = aput.connect("http://localhost:8000", ["v1", "v1000"])
    assert isinstance(api, FlightPathServerApiV1)


def test_connect_unimplemented_version_raises_module_not_found():
    """When no offered version has a local implementation, ModuleNotFoundError
    is raised (not ApiException — the source was refactored)."""
    with pytest.raises(ModuleNotFoundError):
        aput.connect("http://localhost:8000", ["v1000"])


def test_connect_invalid_version_string_raises_value_error():
    """Malformed version strings propagate ValueError from _parse_versions
    before connect even attempts to load an implementation."""
    with pytest.raises(ValueError):
        aput.connect("http://localhost:8000", ["bad"])
