"""
Unit tests for OsUtility (flightpath/util/os_utility.py).

Covers:
  is_sandboxed        — checks APP_SANDBOX_CONTAINER_ID environment variable
  is_windows          — sys.platform == "win32"
  is_mac              — sys.platform == "darwin"
  is_unix             — not mac and not windows
  file_system_open_cmd — platform-dependent shell open command

open_file() is excluded: it spawns a subprocess or calls os.startfile() and
cannot be tested safely in CI.

Run with:
  poetry run python -m pytest tests/test_os_utility.py -v
"""

import sys

import pytest

from flightpath.util.os_utility import OsUtility as osut


# ---------------------------------------------------------------------------
# is_sandboxed
# ---------------------------------------------------------------------------


def test_is_sandboxed_returns_true_when_env_var_set(monkeypatch):
    monkeypatch.setenv("APP_SANDBOX_CONTAINER_ID", "fake-container-id")
    assert osut.is_sandboxed() is True


def test_is_sandboxed_returns_false_when_env_var_absent(monkeypatch):
    monkeypatch.delenv("APP_SANDBOX_CONTAINER_ID", raising=False)
    assert osut.is_sandboxed() is False


def test_is_sandboxed_returns_false_for_empty_string_value(monkeypatch):
    """An empty string is still a set env var — but `is not None` makes it True."""
    monkeypatch.setenv("APP_SANDBOX_CONTAINER_ID", "")
    assert osut.is_sandboxed() is True


# ---------------------------------------------------------------------------
# is_windows
# ---------------------------------------------------------------------------


def test_is_windows_returns_true_on_win32(monkeypatch):
    monkeypatch.setattr(sys, "platform", "win32")
    assert osut.is_windows() is True


def test_is_windows_returns_false_on_darwin(monkeypatch):
    monkeypatch.setattr(sys, "platform", "darwin")
    assert osut.is_windows() is False


def test_is_windows_returns_false_on_linux(monkeypatch):
    monkeypatch.setattr(sys, "platform", "linux")
    assert osut.is_windows() is False


# ---------------------------------------------------------------------------
# is_mac
# ---------------------------------------------------------------------------


def test_is_mac_returns_true_on_darwin(monkeypatch):
    monkeypatch.setattr(sys, "platform", "darwin")
    assert osut.is_mac() is True


def test_is_mac_returns_false_on_win32(monkeypatch):
    monkeypatch.setattr(sys, "platform", "win32")
    assert osut.is_mac() is False


def test_is_mac_returns_false_on_linux(monkeypatch):
    monkeypatch.setattr(sys, "platform", "linux")
    assert osut.is_mac() is False


# ---------------------------------------------------------------------------
# is_unix
# ---------------------------------------------------------------------------


def test_is_unix_returns_true_on_linux(monkeypatch):
    monkeypatch.setattr(sys, "platform", "linux")
    assert osut.is_unix() is True


def test_is_unix_returns_false_on_darwin(monkeypatch):
    monkeypatch.setattr(sys, "platform", "darwin")
    assert osut.is_unix() is False


def test_is_unix_returns_false_on_win32(monkeypatch):
    monkeypatch.setattr(sys, "platform", "win32")
    assert osut.is_unix() is False


# ---------------------------------------------------------------------------
# file_system_open_cmd
# ---------------------------------------------------------------------------


def test_file_system_open_cmd_returns_open_on_mac(monkeypatch):
    monkeypatch.setattr(sys, "platform", "darwin")
    assert osut.file_system_open_cmd() == "open"


def test_file_system_open_cmd_returns_explorer_on_windows(monkeypatch):
    monkeypatch.setattr(sys, "platform", "win32")
    assert osut.file_system_open_cmd() == "explorer"


def test_file_system_open_cmd_returns_xdg_open_on_linux(monkeypatch):
    monkeypatch.setattr(sys, "platform", "linux")
    assert osut.file_system_open_cmd() == "xdg-open"
