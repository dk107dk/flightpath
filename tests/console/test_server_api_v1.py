"""
Unit tests for FlightPathServerApiV1 result-parsing logic
(flightpath/util/api/v1.py).

These tests focus on the logic that runs AFTER the HTTP call returns —
base64 decoding, dict extraction, error pass-through — not on the HTTP
transport itself.  _post and _get are replaced with simple lambdas that
return pre-built Result tuples.

Known bug pinned here:
  get_project_names() calls Result(True, data["names"], status_code) with
  only 3 positional args.  Result has 4 fields (success, data,
  error_message, status_code), so the integer status code lands in
  error_message and status_code is left as None.

Run with:
  poetry run python -m pytest tests/test_server_api_v1.py -v
"""

import base64

import pytest

from flightpath.util.api.v1 import FlightPathServerApiV1
from flightpath.util.api.server_api import Result


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _api(monkeypatch, *, post_result=None, get_result=None):
    """Return a V1 instance with _post and/or _get replaced by stubs."""
    api = FlightPathServerApiV1("http://test")
    if post_result is not None:
        monkeypatch.setattr(api, "_post", lambda *a, **kw: post_result)
    if get_result is not None:
        monkeypatch.setattr(api, "_get", lambda *a, **kw: get_result)
    return api


def _encoded(text: str) -> str:
    return base64.b64encode(text.encode()).decode()


# ---------------------------------------------------------------------------
# download_log
# ---------------------------------------------------------------------------


def test_download_log_failure_passes_through(monkeypatch):
    failure = Result(False, None, "connection error", -1)
    api = _api(monkeypatch, post_result=failure)
    result = api.download_log("myproject")
    assert result.success is False
    assert result.error_message == "connection error"


def test_download_log_success_decodes_base64_content(monkeypatch):
    payload = {"file_content": _encoded("line1\nline2\n")}
    api = _api(monkeypatch, post_result=Result(True, payload, None, 200))
    result = api.download_log("myproject")
    assert result.success is True
    assert result.data == "line1\nline2\n"


def test_download_log_missing_file_content_key_returns_failure(monkeypatch):
    payload = {"other_key": "value"}
    api = _api(monkeypatch, post_result=Result(True, payload, None, 200))
    result = api.download_log("myproject")
    assert result.success is False
    assert "file_content" in result.error_message


def test_download_log_data_not_dict_returns_failure(monkeypatch):
    """When data is not a dict (e.g. a plain string), file_content lookup returns None."""
    api = _api(monkeypatch, post_result=Result(True, "unexpected string", None, 200))
    result = api.download_log("myproject")
    assert result.success is False


def test_download_log_invalid_base64_returns_failure(monkeypatch):
    payload = {"file_content": "!!!not-valid-base64!!!"}
    api = _api(monkeypatch, post_result=Result(True, payload, None, 200))
    result = api.download_log("myproject")
    assert result.success is False
    assert "Could not decode" in result.error_message


def test_download_log_valid_unicode_content(monkeypatch):
    """Log content with unicode characters must round-trip cleanly."""
    log_text = "résumé: ✓ passed\n"
    payload = {"file_content": _encoded(log_text)}
    api = _api(monkeypatch, post_result=Result(True, payload, None, 200))
    result = api.download_log("myproject")
    assert result.success is True
    assert result.data == log_text


# ---------------------------------------------------------------------------
# get_project_names
# ---------------------------------------------------------------------------


def test_get_project_names_failure_passes_through(monkeypatch):
    failure = Result(False, None, "timeout", -1)
    api = _api(monkeypatch, post_result=failure)
    result = api.get_project_names()
    assert result.success is False
    assert result.error_message == "timeout"


def test_get_project_names_success_returns_names_list(monkeypatch):
    payload = {"names": ["alpha", "beta", "gamma"]}
    api = _api(monkeypatch, post_result=Result(True, payload, None, 200))
    result = api.get_project_names()
    assert result.success is True
    assert result.data == ["alpha", "beta", "gamma"]


def test_get_project_names_unexpected_response_returns_failure(monkeypatch):
    """When data dict has no 'names' key the method returns a failure Result."""
    payload = {"projects": ["alpha"]}
    api = _api(monkeypatch, post_result=Result(True, payload, None, 200))
    result = api.get_project_names()
    assert result.success is False
    assert "Unexpected response" in result.error_message


def test_get_project_names_result_has_correct_fields(monkeypatch):
    payload = {"names": ["alpha"]}
    api = _api(monkeypatch, post_result=Result(True, payload, None, 200))
    result = api.get_project_names()
    assert result.success is True
    assert result.error_message is None
    assert result.status_code == 200
