"""
Unit tests for FlightPathServerApi shared methods
(flightpath/util/api/server_api.py).

Covers _to_result, _url, and the headers/key properties.
No HTTP mocking is needed: httpx.Response can be constructed directly
for test purposes.

Uses FlightPathServerApiV1 as a concrete stand-in so that __new__ skips
the factory branch (which tries to contact a real server).

Known bug pinned here:
  FlightPathServerApi.discover() returns a plain tuple (not a Result) in
  its outermost except branch.  The caller in __new__ does res.success,
  which raises AttributeError on a plain tuple.

Run with:
  poetry run python -m pytest tests/test_server_api.py -v
"""

import httpx
import pytest

from flightpath.util.api.v1 import FlightPathServerApiV1
from flightpath.util.api.server_api import Result


# ---------------------------------------------------------------------------
# Fixture
# ---------------------------------------------------------------------------


@pytest.fixture
def api():
    """A concrete V1 instance that bypasses the version-discovery factory."""
    return FlightPathServerApiV1("http://test:8000")


# ---------------------------------------------------------------------------
# _to_result — 2xx success paths
# ---------------------------------------------------------------------------


def test_to_result_200_json_returns_success_result(api):
    response = httpx.Response(200, json={"status": "ok"})
    result = api._to_result(response)
    assert result.success is True
    assert result.data == {"status": "ok"}
    assert result.error_message is None
    assert result.status_code == 200


def test_to_result_201_is_also_success(api):
    response = httpx.Response(201, json={"id": 42})
    result = api._to_result(response)
    assert result.success is True
    assert result.status_code == 201


def test_to_result_299_is_last_success_code(api):
    response = httpx.Response(299, json={})
    assert api._to_result(response).success is True


def test_to_result_200_non_json_body_returns_text(api):
    """When a 200 has a non-JSON body, result.data is the raw text string."""
    response = httpx.Response(200, content=b"pong")
    result = api._to_result(response)
    assert result.success is True
    assert result.data == "pong"


# ---------------------------------------------------------------------------
# _to_result — failure paths
# ---------------------------------------------------------------------------


def test_to_result_300_is_not_success(api):
    """300-level responses are outside the 200–299 window → failure."""
    response = httpx.Response(300, json={})
    assert api._to_result(response).success is False


def test_to_result_400_with_detail_includes_detail_in_message(api):
    response = httpx.Response(400, json={"detail": "field required"})
    result = api._to_result(response)
    assert result.success is False
    assert "field required" in result.error_message
    assert result.status_code == 400


def test_to_result_400_with_message_key_includes_message(api):
    response = httpx.Response(400, json={"message": "bad input"})
    result = api._to_result(response)
    assert result.success is False
    assert "bad input" in result.error_message


def test_to_result_400_non_json_body_uses_generic_message(api):
    response = httpx.Response(400, content=b"not json at all")
    result = api._to_result(response)
    assert result.success is False
    assert "400" in result.error_message
    assert result.data is None


def test_to_result_500_returns_failure(api):
    response = httpx.Response(500, json={"detail": "internal error"})
    result = api._to_result(response)
    assert result.success is False
    assert result.status_code == 500


def test_to_result_failure_result_has_none_data(api):
    response = httpx.Response(404, json={"detail": "not found"})
    result = api._to_result(response)
    assert result.data is None


# ---------------------------------------------------------------------------
# _url
# ---------------------------------------------------------------------------


def test_url_no_leading_slash(api):
    assert api._url("admin/ping") == "http://test:8000/admin/ping"


def test_url_leading_slash_is_stripped(api):
    """A leading slash on path must not create a double slash."""
    assert api._url("/admin/ping") == "http://test:8000/admin/ping"


def test_url_empty_path(api):
    assert api._url("") == "http://test:8000/"


# ---------------------------------------------------------------------------
# headers property and key setter
# ---------------------------------------------------------------------------


def test_headers_contains_content_type(api):
    assert api.headers["Content-Type"] == "application/json"


def test_headers_access_token_is_none_initially(api):
    assert api.headers["access_token"] is None


def test_headers_reflects_key_after_set(api):
    api.key = "my-secret-key"
    assert api.headers["access_token"] == "my-secret-key"


def test_key_setter_and_getter_roundtrip(api):
    api.key = "abc123"
    assert api.key == "abc123"


# ---------------------------------------------------------------------------
# discover() bare-tuple bug (documented, not triggered by test)
# ---------------------------------------------------------------------------


def test_result_namedtuple_has_success_attribute():
    """
    This test documents why the discover() bare-tuple bug matters.

    discover() returns `(False, None, msg, -1)` on unknown exceptions instead
    of `Result(False, None, msg, -1)`.  The caller in __new__ does res.success,
    which works on a Result NamedTuple but raises AttributeError on a plain
    tuple.  Verified here: a plain tuple has no .success attribute.
    """
    plain = (False, None, "error", -1)
    named = Result(False, None, "error", -1)
    assert named.success is False
    with pytest.raises(AttributeError):
        _ = plain.success
