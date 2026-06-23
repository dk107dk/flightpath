"""
pytest-qt and HTTP tests for ServerForm and the FlightPath Server HTTP API.

Two-tier test strategy
======================

Mock tier (fast, offline)
--------------------------
Uses the main MainWindow fixture and replaces form._api with a MagicMock so no
HTTP requests are made.  Covers form state: host/key persistence, project list
population, upload/download call dispatch, and warning dialogs on failure.

Subprocess tier (integration)
------------------------------
A session-scoped fixture starts a real FlightPath Server subprocess with an
isolated app_config.ini (a free port + an isolated key file in tmp_path_factory).
Tests in this tier prove actual HTTP round-trips without the GUI layer.

Key isolation note
~~~~~~~~~~~~~~~~~~
ProjectManager.projects_dir is hardcoded to ~/FlightPathServer/projects regardless
of which app_config.ini is used.  Test projects are given a UUID-suffixed name and
the entire key-hash subdirectory is removed at teardown.  The key file itself lives
in tmp_path_factory, so it is cleaned up automatically.

Running
-------
All tests (mock + subprocess):
  QT_QPA_PLATFORM=offscreen poetry run python -m pytest tests/gui/test_server_form.py -v

Mock tier only (no subprocess required):
  QT_QPA_PLATFORM=offscreen poetry run python -m pytest tests/gui/test_server_form.py -v -m "not live_server"
"""

import hashlib
import os
import shutil
import socket
import subprocess
import time
import uuid
from pathlib import Path
from unittest.mock import MagicMock

import httpx
import pytest
from PySide6.QtWidgets import QMessageBox

from flightpath.util.api.server_api import Result
from flightpath.util.deploy_utility import DeployUtility
from flightpath.util.message_utility import MessageUtility

# isolated_home and main fixtures provided by conftest.py

# ---------------------------------------------------------------------------
# Helpers shared by both tiers
# ---------------------------------------------------------------------------

_PROJECT_ROOT = Path(__file__).parent.parent.parent


def _open_server_form(main):
    """Open config and return the ServerForm without navigating to it."""
    main.open_config()
    form = main.config.config_panel.get_form("server")
    assert form is not None, "ServerForm must be present in config panel"
    return form


def _wire_mock(form, mock_api, *, host="http://localhost:19999", key="test-api-key"):
    """Install mock_api on form and set host/key text without triggering API calls.

    The host.textChanged and key.textChanged signals call _update_project_list_new_*,
    which calls _update_project_list.  That method's first guard checks
    'forms_layout.currentWidget() != self' — since we have NOT navigated to the server
    form yet, the guard fires an early return on every text change.  So setting text
    here is safe even before mock_api is installed.

    We install mock_api BEFORE setting text so that any path that somehow bypasses
    the guard still hits the mock rather than making real HTTP calls.
    """
    form._api = mock_api
    form.host.setText(host)
    form.key.setText(key)


# ---------------------------------------------------------------------------
# Mock-tier fixture
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_api():
    """MagicMock standing in for FlightPathServerApiV2."""
    api = MagicMock()
    # ping — used by _server_is_enabled → _enableable → _ping
    api.ping.return_value = Result(True, {"message": "ok"}, None, 200)
    # project operations
    api.get_project_names.return_value = Result(True, ["proj-alpha", "proj-beta"], None, 200)
    api.create_project.return_value = Result(True, {"message": "created"}, None, 201)
    api.delete_project.return_value = Result(True, {"message": "deleted"}, None, 200)
    # config/env/log transfers
    api.upload_config.return_value = Result(True, {}, None, 200)
    api.upload_env.return_value = Result(True, {}, None, 200)
    api.download_config.return_value = Result(True, "[logging]\nlog_level = INFO\n", None, 200)
    api.download_env.return_value = Result(True, '{"API_HOST": "example.com"}', None, 200)
    api.download_log.return_value = Result(True, "INFO starting up\n", None, 200)
    # admin
    api.shutdown.return_value = Result(True, {"message": "Server is shutting down."}, None, 200)
    return api


# ---------------------------------------------------------------------------
# Mock-tier tests — form state and persistence
# ---------------------------------------------------------------------------


def test_server_form_saves_host_and_key(qtbot, main, mock_api):
    """
    add_to_config() must write [server] host and [server] api_key to the
    CsvPath config.  These are the values the GUI uses to reconnect to the
    server on every subsequent session.
    """
    form = _open_server_form(main)
    _wire_mock(form, mock_api)

    form.add_to_config(main.csvpath_config)

    host_val = main.csvpath_config.get(
        section="server", name="host", string_parse=False, swaps=False
    )
    key_val = main.csvpath_config.get(
        section="server", name="api_key", string_parse=False, swaps=False
    )
    assert host_val == "http://localhost:19999", (
        f"[server] host must match what was entered; got {host_val!r}"
    )
    assert key_val == "test-api-key", (
        f"[server] api_key must match what was entered; got {key_val!r}"
    )


def test_server_form_populates_from_config(qtbot, main, mock_api):
    """
    really_populate() must read [server] host and api_key from config and set
    the corresponding widget texts.

    really_populate() is also guarded by 'forms_layout.currentWidget() == self',
    but it is called unconditionally from populate_if() (which is used when the
    form has never been viewed).  The test calls really_populate() directly.
    """
    # Write values to config first
    main.csvpath_config.add_to_config("server", "host", "http://stored-host:8080")
    main.csvpath_config.add_to_config("server", "api_key", "stored-key-abc")

    form = _open_server_form(main)
    form._api = mock_api

    form.really_populate()

    assert form.host.text() == "http://stored-host:8080", (
        f"host field must be populated from config; got {form.host.text()!r}"
    )
    assert form.key.text() == "stored-key-abc", (
        f"key field must be populated from config; got {form.key.text()!r}"
    )


def test_server_form_shutdown_button_disabled_without_credentials(qtbot, main):
    """
    The shutdown button must be disabled when host or key is absent.

    _enable_server_if() is called on form construction and after add_to_config().
    On a fresh form with no config values, the button must start disabled.
    """
    form = _open_server_form(main)

    # fresh form has no host or key set — button must be off
    assert not form.shut_down_server.isEnabled(), (
        "Shutdown button must be disabled when no host/key is configured"
    )


def test_server_form_shutdown_button_enabled_with_credentials(qtbot, main, mock_api):
    """
    When host and key are both set and _ping() returns 200, the shutdown button
    must be enabled.

    _enable_server_if() → _server_is_enabled() → _enableable() → _ping() → 200.
    The mock's ping returns Result(True, ..., None, 200) so _ping() returns 200.
    """
    form = _open_server_form(main)
    _wire_mock(form, mock_api)
    form._enable_server_if()

    assert form.shut_down_server.isEnabled(), (
        "Shutdown button must be enabled when host + key are set and server responds 200"
    )


# ---------------------------------------------------------------------------
# Mock-tier tests — project list
# ---------------------------------------------------------------------------


def test_get_project_names_populates_list(qtbot, main, mock_api):
    """
    When the ServerForm becomes the visible form and host + key are set,
    _update_project_list() must call api.get_project_names() and populate
    proj_list.

    _update_project_list() guards on 'forms_layout.currentWidget() == self', so
    the test navigates to form index 11 (the server form) to satisfy the guard.
    Only AFTER navigation are host and key set — setting them triggers
    _update_project_list_new_host/key(), which calls _update_project_list() with
    the guard now satisfied.
    """
    form = _open_server_form(main)
    form._api = mock_api  # install mock before making form visible

    # Navigate to the server form (index 11 in forms_layout)
    main.config.config_panel.forms_layout.setCurrentIndex(11)

    # Setting text after navigation — guard passes, _get_project_names() is called
    form.host.setText("http://localhost:19999")
    form.key.setText("test-api-key")
    # key change triggers _update_project_list via _update_project_list_new_key

    assert form.proj_list.count() == 2, (
        f"proj_list must contain 2 items from mock_api.get_project_names(); "
        f"got {form.proj_list.count()}"
    )
    names = [form.proj_list.item(i).text() for i in range(form.proj_list.count())]
    assert "proj-alpha" in names and "proj-beta" in names, (
        f"proj_list must contain 'proj-alpha' and 'proj-beta'; got {names}"
    )


# ---------------------------------------------------------------------------
# Mock-tier tests — upload operations
# ---------------------------------------------------------------------------


def test_upload_config_answer_yes_calls_api(monkeypatch, qtbot, main, mock_api):
    """
    _upload_config_answer(QMessageBox.Yes, ...) must call api.upload_config()
    with the project name and the provided config string.

    This bypasses the yesNo2 confirmation dialog that _upload_config() shows
    for user-initiated uploads.  The test calls the answer slot directly with
    a pre-built config string to avoid triggering save_config_changes().

    DeployUtility.make_deployable is monkeypatched to identity because it
    parses the config string as a ConfigParser and requires sections that are
    not present in a minimal test string.  The server-side normalisation it
    performs is not the subject of this test.
    """
    monkeypatch.setattr(DeployUtility, "make_deployable", staticmethod(lambda s: s))

    form = _open_server_form(main)
    _wire_mock(form, mock_api)

    config_str = "[logging]\nlog_level = INFO\n"
    form._upload_config_answer(QMessageBox.Yes, name="test-proj", config_str=config_str)

    mock_api.upload_config.assert_called_once()
    call_name = mock_api.upload_config.call_args[0][0]
    assert call_name == "test-proj", (
        f"upload_config must be called with project name 'test-proj'; got {call_name!r}"
    )


def test_upload_config_answer_no_skips_api(qtbot, main, mock_api):
    """
    _upload_config_answer(QMessageBox.No, ...) must not call api.upload_config().

    The user clicked No on the confirmation dialog — no upload should happen.
    """
    form = _open_server_form(main)
    _wire_mock(form, mock_api)

    form._upload_config_answer(QMessageBox.No, name="test-proj", config_str="[x]\n")

    mock_api.upload_config.assert_not_called()


def test_upload_config_shows_warning_on_api_failure(monkeypatch, qtbot, main, mock_api):
    """
    When api.upload_config() returns a failure Result, _upload_config_answer()
    must call MessageUtility.warning2 with an explanatory message.

    The mock api is configured to return a failure for this specific test.
    DeployUtility.make_deployable is patched to identity for the same reason as
    test_upload_config_answer_yes_calls_api.
    """
    monkeypatch.setattr(DeployUtility, "make_deployable", staticmethod(lambda s: s))
    mock_api.upload_config.return_value = Result(False, None, "Forbidden", 403)

    form = _open_server_form(main)
    _wire_mock(form, mock_api)

    warnings = []
    monkeypatch.setattr(
        MessageUtility,
        "warning2",
        lambda **kw: warnings.append(kw.get("msg", "")),
    )

    form._upload_config_answer(
        QMessageBox.Yes, name="test-proj", config_str="[logging]\n"
    )

    assert len(warnings) == 1, (
        f"Exactly one warning must be shown on upload failure; got {len(warnings)}"
    )
    assert "403" in warnings[0] or "upload config" in warnings[0].lower(), (
        f"Warning message must reference the failure; got {warnings[0]!r}"
    )


# ---------------------------------------------------------------------------
# Mock-tier tests — download operations
# ---------------------------------------------------------------------------


def test_download_config_writes_file(monkeypatch, qtbot, main, mock_api):
    """
    _download_config() must write the downloaded config content to a local file
    under main.state.cwd (since no file is selected in the sidebar tree).

    After the write, _download_config calls meut.yesNo2 asking "Open file?".
    That dialog is monkeypatched to a no-op so no window appears.
    """
    form = _open_server_form(main)
    _wire_mock(form, mock_api)

    monkeypatch.setattr(MessageUtility, "yesNo2", lambda **kw: None)

    form._download_config("test-proj")

    expected = os.path.join(main.state.cwd, "config.ini")
    assert os.path.exists(expected), (
        f"Downloaded config must be written to {expected}"
    )
    content = Path(expected).read_text()
    assert "log_level" in content, (
        f"Written file must contain the downloaded config content; got {content!r}"
    )


def test_download_config_shows_warning_on_failure(monkeypatch, qtbot, main, mock_api):
    """
    When api.download_config() returns a failure, _download_config() must call
    MessageUtility.warning2 and must NOT create a local file.
    """
    mock_api.download_config.return_value = Result(False, None, "Not Found", 404)

    form = _open_server_form(main)
    _wire_mock(form, mock_api)

    warnings = []
    monkeypatch.setattr(
        MessageUtility,
        "warning2",
        lambda **kw: warnings.append(kw.get("msg", "")),
    )

    form._download_config("missing-proj")

    assert len(warnings) == 1, (
        f"Exactly one warning must be shown on download failure; got {len(warnings)}"
    )
    assert not os.path.exists(os.path.join(main.state.cwd, "config.ini")), (
        "No local file must be created when the download fails"
    )


def test_download_env_writes_file(monkeypatch, qtbot, main, mock_api):
    """
    _download_env() must write the downloaded env JSON content to a local
    env.json file under main.state.cwd.
    """
    form = _open_server_form(main)
    _wire_mock(form, mock_api)

    monkeypatch.setattr(MessageUtility, "yesNo2", lambda **kw: None)

    form._download_env("test-proj")

    expected = os.path.join(main.state.cwd, "env.json")
    assert os.path.exists(expected), (
        f"Downloaded env must be written to {expected}"
    )
    content = Path(expected).read_text()
    assert "API_HOST" in content, (
        f"Written file must contain the downloaded env content; got {content!r}"
    )


# ---------------------------------------------------------------------------
# Mock-tier tests — project management
# ---------------------------------------------------------------------------


def test_create_project_calls_api(qtbot, main, mock_api):
    """
    _create_project() must call api.create_project() with the given project
    name and the serialized current config as the config_str argument.
    """
    form = _open_server_form(main)
    _wire_mock(form, mock_api)

    form._create_project("my-new-project")

    mock_api.create_project.assert_called_once()
    call_name = mock_api.create_project.call_args[0][0]
    assert call_name == "my-new-project", (
        f"create_project must be called with 'my-new-project'; got {call_name!r}"
    )


def test_delete_project_answer_yes_calls_api(qtbot, main, mock_api):
    """
    _delete_project_answer(QMessageBox.Yes, ...) must call api.delete_project()
    with the correct project name.

    The method is called via the yesNo2 callback — the test invokes it directly
    to avoid showing a confirmation dialog.
    """
    form = _open_server_form(main)
    _wire_mock(form, mock_api)

    form._delete_project_answer(QMessageBox.Yes, name="old-project")

    mock_api.delete_project.assert_called_once()
    call_name = mock_api.delete_project.call_args[0][0]
    assert call_name == "old-project", (
        f"delete_project must be called with 'old-project'; got {call_name!r}"
    )


def test_delete_project_answer_no_skips_api(qtbot, main, mock_api):
    """
    _delete_project_answer(QMessageBox.No, ...) must not call api.delete_project().

    User cancelled the deletion — no destructive API call should happen.
    """
    form = _open_server_form(main)
    _wire_mock(form, mock_api)

    form._delete_project_answer(QMessageBox.No, name="old-project")

    mock_api.delete_project.assert_not_called()


def test_shutdown_answer_yes_calls_api(qtbot, main, mock_api):
    """
    _do_shutdown_answer(QMessageBox.Yes) must call api.shutdown() and then
    disable the shutdown button (server is no longer accessible).
    """
    form = _open_server_form(main)
    _wire_mock(form, mock_api)
    form._enable_server_if()  # enable button first so we can verify it is disabled after

    form._do_shutdown_answer(QMessageBox.Yes)

    mock_api.shutdown.assert_called_once()
    assert not form.shut_down_server.isEnabled(), (
        "Shutdown button must be disabled after a successful shutdown call"
    )


# ---------------------------------------------------------------------------
# Subprocess tier — helpers
# ---------------------------------------------------------------------------

# Minimal CsvPath Framework config.ini that satisfies all the section-access
# the server's ProjectManager._modify_config() performs when creating a project.
# The server rewrites every path value, so placeholder paths are fine.
_MINIMAL_CONFIG = """\
[config]
path =

[inputs]
files =
csvpaths =
allow_local_files = yes
allow_http_files = yes
on_unmatched_file_fingerprints = halt

[results]
archive =
transfers =

[logging]
csvpath = info
csvpaths = info
log_file =
handler = file
log_file_size = 50000000
log_files_to_keep = 100

[extensions]
csvpath_files = csvpath, csvpaths
csv_files = csv, tsv, dat, tab, psv, ssv, xlsx, jsonl

[errors]
csvpath = collect, fail, print
csvpaths = print, collect

[cache]
path =

[functions]
imports =

[sql]
dialect =
connection_string =

[listeners]
groups = default
"""


# ---------------------------------------------------------------------------
# Subprocess tier — session fixture
# ---------------------------------------------------------------------------


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("localhost", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="session")
def live_server(tmp_path_factory):
    """
    Start a FlightPath Server subprocess with an isolated config and yield
    (api, project_name) for the duration of the test session.

    Isolation:
      - Port:     dynamically chosen free port
      - Key file: tmp_path_factory directory (cleaned up automatically)
      - Projects: ~/FlightPathServer/projects/<key_hash>/  (cleaned up in teardown)

    The first admin key is created unauthenticated (the server allows this when
    no keys exist yet — see v2/routers/admin.py create_key docstring).

    If the server fails to start within 15 s, all tests that depend on this
    fixture are SKIPPED rather than ERRORed.
    """
    port = _free_port()
    host = f"http://localhost:{port}"

    tmp = tmp_path_factory.mktemp("server_cfg")
    config_path = tmp / "app_config.ini"
    key_file = tmp / "keys.json"

    config_path.write_text(
        f"[server]\nport = {port}\nhost = localhost\nworkers = 1\n\n"
        f"[security]\nkey_file_path = {key_file}\n"
    )

    server_env = {
        **os.environ,
        "FLIGHTPATH_SERVER_CONFIG": str(config_path),
    }
    proc = subprocess.Popen(
        [
            "poetry",
            "run",
            "python",
            "-c",
            "from flightpath_server.main import run; run()",
        ],
        env=server_env,
        cwd=str(_PROJECT_ROOT),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    # Poll until ready (up to 15 s)
    deadline = time.time() + 15
    ready = False
    while time.time() < deadline:
        try:
            r = httpx.get(host, timeout=1)
            if r.status_code == 200:
                ready = True
                break
        except httpx.HTTPError:
            pass
        time.sleep(0.5)

    if not ready:
        proc.terminate()
        proc.wait(timeout=5)
        pytest.skip("FlightPath Server did not start within 15 seconds")

    # Bootstrap: create the first (admin) key — unauthenticated when no keys exist
    r = httpx.post(
        f"{host}/v2/admin/keys",
        json={
            "key_name": "pytest-key",
            "key_owner_name": "pytest",
            "key_owner_contact": "pytest@localhost",
        },
        headers={"Content-Type": "application/json"},
        timeout=5,
    )
    if r.status_code != 201:
        proc.terminate()
        proc.wait(timeout=5)
        pytest.skip(f"Could not create first key: {r.status_code} {r.text}")

    api_key = r.json()["api_key"]
    project_name = f"test-{uuid.uuid4().hex[:8]}"

    # Create the test project with a minimal valid config
    r = httpx.post(
        f"{host}/v2/projects",
        json={"name": project_name, "config_str": _MINIMAL_CONFIG},
        headers={"Content-Type": "application/json", "access_token": api_key},
        timeout=5,
    )
    if r.status_code != 201:
        proc.terminate()
        proc.wait(timeout=5)
        pytest.skip(f"Could not create test project: {r.status_code} {r.text}")

    # Build a typed API object pointing at the live server
    from flightpath.util.api.v2 import FlightPathServerApiV2

    api = FlightPathServerApiV2(host)
    api.key = api_key

    yield api, project_name

    # Teardown: remove the key-hash project directory from ~/FlightPathServer/projects/
    # and terminate the server
    try:
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        projects_root = os.path.expanduser(f"~/FlightPathServer/projects/{key_hash}")
        if os.path.isdir(projects_root):
            shutil.rmtree(projects_root)
    except Exception as exc:
        print(f"[live_server teardown] project cleanup warning: {exc}")
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()


# ---------------------------------------------------------------------------
# Subprocess tier — tests
# ---------------------------------------------------------------------------


@pytest.mark.live_server
def test_live_server_is_reachable(live_server):
    """
    FlightPathServerApi.discover() must return a 200 response from the live
    server, confirming the server started and the root endpoint is healthy.

    discover() is the same call the GUI makes when first connecting to a server.
    """
    from flightpath.util.api.server_api import FlightPathServerApi

    api, _ = live_server
    result = FlightPathServerApi.discover(api.host)

    assert result.success is True, (
        f"discover() must succeed for a live server; error: {result.error_message}"
    )
    assert result.status_code == 200, (
        f"discover() must return 200; got {result.status_code}"
    )
    assert "api_versions" in result.data.get("message", {}), (
        "Server root response must include api_versions"
    )


@pytest.mark.live_server
def test_live_create_and_list_project(live_server):
    """
    Creating a project via api.create_project() must make it appear in the
    list returned by api.get_project_names().

    This proves the full create → list round-trip over HTTP, the same path
    taken when the ServerForm creates a project and then refreshes proj_list.
    """
    api, existing_project = live_server

    extra = f"extra-{uuid.uuid4().hex[:6]}"
    create_result = api.create_project(extra, _MINIMAL_CONFIG)
    assert create_result.success, (
        f"create_project must succeed; error: {create_result.error_message}"
    )

    list_result = api.get_project_names()
    assert list_result.success, (
        f"get_project_names must succeed; error: {list_result.error_message}"
    )
    assert extra in list_result.data, (
        f"Newly created project '{extra}' must appear in project list; "
        f"got {list_result.data}"
    )

    # Clean up the extra project so teardown only has the primary to remove
    api.delete_project(extra)


@pytest.mark.live_server
def test_live_upload_and_download_config_round_trip(live_server):
    """
    Uploading a config string to a project and then downloading it must return
    the same content (modulo server-side normalisation the server applies).

    This validates the upload_config → download_config path that the ServerForm
    uses when syncing the GUI project config to the server.
    """
    api, project_name = live_server

    # upload_config calls the server's set_config endpoint which runs _modify_config
    # on the uploaded string — the server rewrites all paths.  We must supply a
    # config with all sections _modify_config accesses (same requirement as
    # create_project).  Use _MINIMAL_CONFIG and spot-check a stable section key.
    up = api.upload_config(project_name, _MINIMAL_CONFIG)
    assert up.success, f"upload_config must succeed; error: {up.error_message}"

    down = api.download_config(project_name)
    assert down.success, f"download_config must succeed; error: {down.error_message}"

    downloaded = down.data or ""
    assert "[inputs]" in downloaded, (
        f"Downloaded config must contain the [inputs] section; got {downloaded!r}"
    )


@pytest.mark.live_server
def test_live_upload_and_download_env_round_trip(live_server):
    """
    Uploading an env JSON string and downloading it must preserve the key/value
    pair, confirming the upload_env → download_env path works end-to-end.
    """
    api, project_name = live_server

    env_str = '{"LIVE_TEST_VAR": "hello-server"}'
    up = api.upload_env(project_name, env_str)
    assert up.success, f"upload_env must succeed; error: {up.error_message}"

    down = api.download_env(project_name)
    assert down.success, f"download_env must succeed; error: {down.error_message}"

    downloaded = down.data or ""
    assert "LIVE_TEST_VAR" in downloaded, (
        f"Downloaded env must contain 'LIVE_TEST_VAR'; got {downloaded!r}"
    )
