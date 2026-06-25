"""
Unit tests for FlightPathServerApiV2 result-parsing logic
(flightpath/util/api/v2.py).

Same pattern as test_server_api_v1.py: _post/_get are stubbed so tests
exercise only the post-HTTP logic.

Known bugs pinned here:

1. download_log URL missing f-prefix:
     self._get("/v2/projects/{name}/files/logs/csvpath.log")
   {name} is never interpolated — the literal string "{name}" is sent
   to the server regardless of the name argument.

2. get_project_names 3-arg Result bug (same as V1):
     Result(True, data["names"], status_code)
   status_code integer ends up in error_message; status_code is None.

Run with:
  poetry run python -m pytest tests/test_server_api_v2.py -v
"""

import base64
from unittest.mock import call, patch

import pytest

from flightpath.util.api.v2 import FlightPathServerApiV2
from flightpath.util.api.server_api import Result


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _api(monkeypatch, *, post_result=None, get_result=None, put_result=None):
    api = FlightPathServerApiV2("http://test")
    if post_result is not None:
        monkeypatch.setattr(api, "_post", lambda *a, **kw: post_result)
    if get_result is not None:
        monkeypatch.setattr(api, "_get", lambda *a, **kw: get_result)
    if put_result is not None:
        monkeypatch.setattr(api, "_put", lambda *a, **kw: put_result)
    return api


def _encoded(text: str) -> str:
    return base64.b64encode(text.encode()).decode()


# ---------------------------------------------------------------------------
# download_log
# ---------------------------------------------------------------------------


def test_v2_download_log_failure_passes_through(monkeypatch):
    failure = Result(False, None, "timeout", -1)
    api = _api(monkeypatch, get_result=failure)
    result = api.download_log("myproject")
    assert result.success is False
    assert result.error_message == "timeout"


def test_v2_download_log_success_decodes_base64_content(monkeypatch):
    payload = {"file_content": _encoded("log line 1\nlog line 2\n")}
    api = _api(monkeypatch, get_result=Result(True, payload, None, 200))
    result = api.download_log("myproject")
    assert result.success is True
    assert result.data == "log line 1\nlog line 2\n"


def test_v2_download_log_missing_file_content_returns_failure(monkeypatch):
    api = _api(monkeypatch, get_result=Result(True, {"other": "val"}, None, 200))
    result = api.download_log("myproject")
    assert result.success is False
    assert "file_content" in result.error_message


def test_v2_download_log_invalid_base64_returns_failure(monkeypatch):
    payload = {"file_content": "!!!invalid!!!"}
    api = _api(monkeypatch, get_result=Result(True, payload, None, 200))
    result = api.download_log("myproject")
    assert result.success is False
    assert "Could not decode" in result.error_message


def test_v2_download_log_url_interpolates_project_name(monkeypatch):
    captured = []

    def capture_get(path):
        captured.append(path)
        return Result(True, {"file_content": _encoded("x")}, None, 200)

    api = FlightPathServerApiV2("http://test")
    monkeypatch.setattr(api, "_get", capture_get)
    api.download_log("real_project_name")

    assert len(captured) == 1
    assert "real_project_name" in captured[0]
    assert "{name}" not in captured[0]


# ---------------------------------------------------------------------------
# download_config
# ---------------------------------------------------------------------------


def test_v2_download_config_extracts_value_on_success(monkeypatch):
    payload = {"value": "[config]\nkey=val\n"}
    api = _api(monkeypatch, get_result=Result(True, payload, None, 200))
    result = api.download_config("myproject")
    assert result.success is True
    assert result.data == "[config]\nkey=val\n"


def test_v2_download_config_failure_passes_through_unchanged(monkeypatch):
    failure = Result(False, None, "not found", 404)
    api = _api(monkeypatch, get_result=failure)
    result = api.download_config("myproject")
    assert result.success is False
    assert result.error_message == "not found"
    assert result.status_code == 404


def test_v2_download_config_missing_value_key_returns_none_data(monkeypatch):
    """When the response has no 'value' key, data is replaced with None."""
    payload = {"other": "data"}
    api = _api(monkeypatch, get_result=Result(True, payload, None, 200))
    result = api.download_config("myproject")
    assert result.success is True
    assert result.data is None


# ---------------------------------------------------------------------------
# download_env
# ---------------------------------------------------------------------------


def test_v2_download_env_extracts_value_on_success(monkeypatch):
    payload = {"value": '{"FOO": "bar"}'}
    api = _api(monkeypatch, get_result=Result(True, payload, None, 200))
    result = api.download_env("myproject")
    assert result.success is True
    assert result.data == '{"FOO": "bar"}'


def test_v2_download_env_failure_passes_through(monkeypatch):
    failure = Result(False, None, "server error", 500)
    api = _api(monkeypatch, get_result=failure)
    result = api.download_env("myproject")
    assert result.success is False
    assert result.status_code == 500


def test_v2_download_env_missing_value_key_returns_none_data(monkeypatch):
    api = _api(monkeypatch, get_result=Result(True, {}, None, 200))
    result = api.download_env("myproject")
    assert result.data is None


# ---------------------------------------------------------------------------
# get_project_names
# ---------------------------------------------------------------------------


def test_v2_get_project_names_failure_passes_through(monkeypatch):
    api = _api(monkeypatch, get_result=Result(False, None, "unauthorized", 401))
    result = api.get_project_names()
    assert result.success is False


def test_v2_get_project_names_returns_names_list(monkeypatch):
    payload = {"names": ["proj1", "proj2"]}
    api = _api(monkeypatch, get_result=Result(True, payload, None, 200))
    result = api.get_project_names()
    assert result.success is True
    assert result.data == ["proj1", "proj2"]


def test_v2_get_project_names_missing_names_key_returns_failure(monkeypatch):
    api = _api(monkeypatch, get_result=Result(True, {"items": []}, None, 200))
    result = api.get_project_names()
    assert result.success is False
    assert "Unexpected response" in result.error_message


def test_v2_get_project_names_result_has_correct_fields(monkeypatch):
    payload = {"names": ["proj1"]}
    api = _api(monkeypatch, get_result=Result(True, payload, None, 200))
    result = api.get_project_names()
    assert result.success is True
    assert result.error_message is None
    assert result.status_code == 200
