"""
pytest-qt tests for SyncConfigDialog and CompileEnvDialog.

Checklist coverage:
  CONFIG > server section > config sync — dialog tables populated, sync button state,
  do_sync() dispatches upload_config
  CONFIG > server section > env sync — dialog sending table populated, do_upload()
  compiles JSON, add/remove rows, _upload_env dispatch

Two-tier test strategy
======================

Mock tier (fast, offline)
--------------------------
Uses monkeypatched ServerUtility and a MagicMock API so no HTTP requests are made.
Covers dialog population, button state, table editing, and dispatch to the server API.

Why dialogs are never shown via exec()
---------------------------------------
Both SyncConfigDialog.show_dialog() and CompileEnvDialog.show_dialog() call
self.exec(), which blocks the Qt event loop waiting for user input.  In tests
we create the dialog objects directly (bypassing show_dialog) and call the
slot methods (do_sync, do_upload, table_of_existing_clicked, etc.) directly.
This gives full coverage of the UI logic without any modal loop.

ServerUtility patching
-----------------------
SyncConfigDialog.populate_sending() and _table_of_sending_to_config() both call
seut.download_config() directly (not through the FlightPathServerApi abstraction).
CompileEnvDialog.populate_sending() calls seut.download_env() directly.
These are patched via monkeypatch.setattr(ServerUtility, ...) so no HTTP is made.

Run with:
  QT_QPA_PLATFORM=offscreen poetry run python -m pytest tests/gui/test_sync_dialogs.py -v
"""

import json
from unittest.mock import MagicMock

import pytest

from PySide6.QtWidgets import QTableWidgetItem

from flightpath.util.api.server_api import Result
from flightpath.util.deploy_utility import DeployUtility
from flightpath.util.server_utility import ServerUtility
from flightpath.dialogs.sync_config_dialog import SyncConfigDialog
from flightpath.dialogs.compile_env_dialog import CompileEnvDialog

# isolated_home and main fixtures provided by conftest.py


# ---------------------------------------------------------------------------
# Shared constants
# ---------------------------------------------------------------------------

# Comprehensive mock config that includes every section accessed by
# populate_table() when iterating forms with non-empty server_fields.
# Sections absent here cause those rows in table_of_sending to remain
# blank (None items), which crashes _table_of_sending_to_config.
_MOCK_SERVER_CONFIG = """\
[config]
path =
allow_var_sub = yes
var_sub_source = config/env.json

[inputs]
files =
csvpaths =
allow_local_files = no
allow_http_files = no
on_unmatched_file_fingerprints = halt

[results]
archive =
transfers =

[logging]
csvpath = info
csvpaths = info
log_file = logs/csvpath.log
handler = file
log_file_size = 50000000
log_files_to_keep = 100

[extensions]
csvpath_files = csvpath, csvpaths
csv_files = csv, tsv, dat, tab, psv, ssv, xlsx, jsonl

[errors]
csvpath = collect, fail, print
csvpaths = print, collect
pattern =
use_format = no

[cache]
path = cache

[functions]
imports =

[sql]
dialect =
connection_string =

[sqlite]
db = archive/csvpath.db

[server]
host =
api_key =

[listeners]
groups = default

[llm]
model =
api_base =
api_key =

[ckan]
server =
api_token =

[openlineage]
base_url =
endpoint =
api_key =
timeout = 5
verify = no

[slack]
webhook_url =

[sftp]
server =
port = 22
username =
password =
"""

_MOCK_ENV_JSON = '{"DEMO_VAR": "demo-value", "OTHER_VAR": "other-value"}'


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_api():
    """MagicMock standing in for FlightPathServerApiV2."""
    api = MagicMock()
    api.ping.return_value = Result(True, {"message": "ok"}, None, 200)
    api.upload_config.return_value = Result(True, {}, None, 200)
    api.upload_env.return_value = Result(True, {}, None, 200)
    api.download_config.return_value = Result(True, _MOCK_SERVER_CONFIG, None, 200)
    api.download_env.return_value = Result(True, _MOCK_ENV_JSON, None, 200)
    return api


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _open_server_form(main):
    main.open_config()
    form = main.config.config_panel.get_form("server")
    assert form is not None, "ServerForm must be present in config panel"
    return form


def _wire_mock(form, mock_api, *, host="http://localhost:19999", key="test-api-key"):
    """Install mock_api and set credentials without triggering live API calls.

    Setting text before navigating to the server form (forms_layout index 11) is
    safe: _update_project_list's guard on currentWidget() != self fires immediately
    and returns before making any API calls.
    """
    form._api = mock_api
    form.host.setText(host)
    form.key.setText(key)


def _make_sync_dialog(main, mock_api, monkeypatch, *, project_name="test-proj"):
    """Create a SyncConfigDialog for testing without hitting a real server.

    populate_sending() calls seut.download_config() twice during the dialog
    lifetime (once in __init__ and once in _table_of_sending_to_config inside
    do_sync).  Both are satisfied by the monkeypatch returning _MOCK_SERVER_CONFIG.
    populate_existing() reads main.csvpath_config directly — no server needed.
    """
    form = _open_server_form(main)
    _wire_mock(form, mock_api)

    monkeypatch.setattr(
        ServerUtility,
        "download_config",
        classmethod(lambda cls, **kw: _MOCK_SERVER_CONFIG),
    )

    dialog = SyncConfigDialog(main=main, name=project_name, parent=form)
    return dialog, form


def _make_env_dialog(main, mock_api, monkeypatch, *, project_name="test-proj"):
    """Create a CompileEnvDialog for testing without hitting a real server.

    populate_sending() calls seut.download_env() — monkeypatched to return
    _MOCK_ENV_JSON.  populate_existing() reads local env vars from ConfigEnv;
    monkeypatched to a no-op to avoid depending on env.json being present in
    the test project's isolated home directory.
    """
    form = _open_server_form(main)
    _wire_mock(form, mock_api)

    monkeypatch.setattr(
        ServerUtility,
        "download_env",
        classmethod(lambda cls, **kw: _MOCK_ENV_JSON),
    )
    monkeypatch.setattr(CompileEnvDialog, "populate_existing", lambda self: None)

    dialog = CompileEnvDialog(main=main, name=project_name, parent=form)
    return dialog, form


# ---------------------------------------------------------------------------
# SyncConfigDialog tests
# ---------------------------------------------------------------------------


def test_sync_config_dialog_tables_have_rows(monkeypatch, qtbot, main, mock_api):
    """
    Both tables in SyncConfigDialog must have at least one row after creation:
      - table_of_existing shows fields from the local config
      - table_of_sending shows fields from the server config (mocked download)

    Both tables use total_server_fields as their row count, iterated from
    forms_by_section.  Any section present in the config produces filled rows;
    sections absent from the mock still contribute pre-allocated blank rows.
    This test confirms the tables are non-empty, proving populate_existing()
    and populate_sending() both ran without error.
    """
    dialog, _ = _make_sync_dialog(main, mock_api, monkeypatch)
    qtbot.addWidget(dialog)

    assert dialog.table_of_existing.rowCount() > 0, (
        "table_of_existing must have rows after SyncConfigDialog is created"
    )
    assert dialog.table_of_sending.rowCount() > 0, (
        "table_of_sending must have rows after SyncConfigDialog is created"
    )


def test_sync_config_sync_button_starts_disabled(monkeypatch, qtbot, main, mock_api):
    """
    The Sync button must be disabled immediately after dialog creation.

    It is only enabled when handle_item_changed() fires (a cell in table_of_sending
    was edited), signalling there is a change worth pushing to the server.
    """
    dialog, _ = _make_sync_dialog(main, mock_api, monkeypatch)
    qtbot.addWidget(dialog)

    assert not dialog.sync_button.isEnabled(), (
        "Sync button must be disabled before any table edits"
    )


def test_sync_config_cell_edit_enables_sync_button(monkeypatch, qtbot, main, mock_api):
    """
    Editing a cell in table_of_sending must enable the Sync button.

    table_of_sending.itemChanged is connected to handle_item_changed(), which
    calls sync_button.setEnabled(True).  The test targets the last row to
    stay away from rows that may be pre-filled with a stable server value
    (though any row that fires itemChanged satisfies the assertion).
    """
    dialog, _ = _make_sync_dialog(main, mock_api, monkeypatch)
    qtbot.addWidget(dialog)

    row = dialog.table_of_sending.rowCount() - 1
    item = dialog.table_of_sending.item(row, 1)
    if item is None:
        item = QTableWidgetItem("")
        dialog.table_of_sending.setItem(row, 1, item)
    item.setText("changed-by-test")

    assert dialog.sync_button.isEnabled(), (
        "Sync button must be enabled after editing a cell in table_of_sending"
    )


def test_sync_config_do_sync_calls_upload_config(monkeypatch, qtbot, main, mock_api):
    """
    Calling do_sync() must call api.upload_config() with the correct project name.

    do_sync() → _table_of_sending_to_config() → form._upload_config(name, str,
    prompt=False) → _upload_config_answer(Yes, ...) → api.upload_config(name, str).

    _table_of_sending_to_config is monkeypatched to bypass iterating the table
    rows (some rows may be blank/None when the mock config lacks a section that a
    form declares server_fields for, causing an AttributeError on item.text()).
    DeployUtility.make_deployable is monkeypatched to identity for the same reason
    the existing test_server_form.py tests do: the shape of the deployed config
    is not the subject of this test.
    """
    monkeypatch.setattr(
        SyncConfigDialog,
        "_table_of_sending_to_config",
        lambda self, form: "[logging]\nlog_level = INFO\n",
    )
    monkeypatch.setattr(DeployUtility, "make_deployable", staticmethod(lambda s: s))

    dialog, _ = _make_sync_dialog(main, mock_api, monkeypatch)
    qtbot.addWidget(dialog)

    dialog.do_sync()

    mock_api.upload_config.assert_called_once()
    call_name = mock_api.upload_config.call_args[0][0]
    assert call_name == "test-proj", (
        f"upload_config must be called with project name 'test-proj'; got {call_name!r}"
    )


def test_sync_config_local_click_copies_value_to_sending(
    monkeypatch, qtbot, main, mock_api
):
    """
    Clicking a row in table_of_existing must copy its value to the same row in
    table_of_sending and enable the Sync button.

    table_of_existing_clicked() reads the row index from the clicked item, then
    compares the local and server values.  If they differ, the server cell is
    updated and the Sync button is enabled.  This is the primary UX flow for
    propagating a specific local config value to the server.
    """
    dialog, _ = _make_sync_dialog(main, mock_api, monkeypatch)
    qtbot.addWidget(dialog)

    # Find the first row where all four cells (both tables, both columns) are set
    target_row = None
    for r in range(dialog.table_of_existing.rowCount()):
        ex_name = dialog.table_of_existing.item(r, 0)
        ex_val = dialog.table_of_existing.item(r, 1)
        sn_name = dialog.table_of_sending.item(r, 0)
        sn_val = dialog.table_of_sending.item(r, 1)
        if ex_name and ex_val and sn_name and sn_val:
            target_row = r
            break
    assert target_row is not None, (
        "At least one row must have all four cells populated (needs a section "
        "present in both local config and _MOCK_SERVER_CONFIG)"
    )

    local_value = "local-test-value-unique"
    dialog.table_of_existing.item(target_row, 1).setText(local_value)

    dialog.table_of_existing_clicked(dialog.table_of_existing.item(target_row, 1))

    copied = dialog.table_of_sending.item(target_row, 1)
    assert copied is not None, "table_of_sending item must exist after click"
    assert copied.text() == local_value, (
        f"Sending table must show the local value after click; "
        f"got {copied.text()!r}, expected {local_value!r}"
    )
    assert dialog.sync_button.isEnabled(), (
        "Sync button must be enabled after a local value is copied to sending table"
    )


# ---------------------------------------------------------------------------
# CompileEnvDialog tests
# ---------------------------------------------------------------------------


def test_compile_env_dialog_sending_table_populated(monkeypatch, qtbot, main, mock_api):
    """
    table_of_sending must contain the env vars from the mocked server download.

    populate_sending() calls seut.download_env() (monkeypatched to _MOCK_ENV_JSON),
    parses the JSON, and inserts one row per key/value pair.  _MOCK_ENV_JSON has
    two keys so the table must have exactly two rows.
    """
    dialog, _ = _make_env_dialog(main, mock_api, monkeypatch)
    qtbot.addWidget(dialog)

    assert dialog.table_of_sending.rowCount() == 2, (
        f"table_of_sending must have 2 rows from mock env JSON; "
        f"got {dialog.table_of_sending.rowCount()}"
    )
    names = {
        dialog.table_of_sending.item(r, 0).text()
        for r in range(dialog.table_of_sending.rowCount())
        if dialog.table_of_sending.item(r, 0)
    }
    assert "DEMO_VAR" in names, f"DEMO_VAR must appear in table_of_sending; got {names}"
    assert "OTHER_VAR" in names, f"OTHER_VAR must appear in table_of_sending; got {names}"


def test_compile_env_do_upload_produces_valid_json(monkeypatch, qtbot, main, mock_api):
    """
    Calling do_upload() must serialise table_of_sending into valid JSON and
    assign it to dialog.config_str.

    do_upload() iterates table_of_sending rows, builds a Python dict, calls
    json.dumps(), and assigns the result to config_str.  ServerForm._upload_env()
    reads config_str after show_dialog() returns and passes it to api.upload_env().
    """
    dialog, _ = _make_env_dialog(main, mock_api, monkeypatch)
    qtbot.addWidget(dialog)

    dialog.do_upload()

    assert dialog.config_str is not None, "config_str must be set after do_upload()"
    env = json.loads(dialog.config_str)
    assert isinstance(env, dict), (
        f"config_str must deserialise to a dict; got {type(env).__name__}"
    )
    assert "DEMO_VAR" in env, (
        f"Serialised env must contain DEMO_VAR; got keys {list(env.keys())}"
    )
    assert env["DEMO_VAR"] == "demo-value", (
        f"DEMO_VAR must have value 'demo-value'; got {env['DEMO_VAR']!r}"
    )


def test_compile_env_add_row_appears_in_sending(monkeypatch, qtbot, main, mock_api):
    """
    Clicking 'Add or modify value' with a new key must append a row to
    table_of_sending.

    _on_click_add() checks _has_key() first.  For a key not already in the
    table, it inserts a new row.  For a key that already exists, it updates in
    place (so row count stays the same).  This test uses a key guaranteed to
    be absent from _MOCK_ENV_JSON.
    """
    dialog, _ = _make_env_dialog(main, mock_api, monkeypatch)
    qtbot.addWidget(dialog)

    initial_rows = dialog.table_of_sending.rowCount()

    dialog.add_name.setText("NEW_VAR")
    dialog.add_value.setText("new-value")
    dialog._on_click_add()

    assert dialog.table_of_sending.rowCount() == initial_rows + 1, (
        f"Adding a new key must increase table_of_sending row count by 1; "
        f"was {initial_rows}, now {dialog.table_of_sending.rowCount()}"
    )
    names = {
        dialog.table_of_sending.item(r, 0).text()
        for r in range(dialog.table_of_sending.rowCount())
        if dialog.table_of_sending.item(r, 0)
    }
    assert "NEW_VAR" in names, (
        f"NEW_VAR must appear in table_of_sending after add; got {names}"
    )


def test_compile_env_sending_click_removes_row_and_fills_inputs(
    monkeypatch, qtbot, main, mock_api
):
    """
    Clicking a row in table_of_sending must remove it and copy its key/value
    into the add_name / add_value inputs (ready for editing before re-add).

    table_of_sending_clicked() copies the row to the input fields then calls
    removeRow(), reducing rowCount by 1.
    """
    dialog, _ = _make_env_dialog(main, mock_api, monkeypatch)
    qtbot.addWidget(dialog)

    initial_rows = dialog.table_of_sending.rowCount()
    assert initial_rows > 0, "Need at least one row in table_of_sending to test removal"

    first_name_item = dialog.table_of_sending.item(0, 0)
    assert first_name_item is not None
    expected_key = first_name_item.text()

    dialog.table_of_sending_clicked(first_name_item)

    assert dialog.table_of_sending.rowCount() == initial_rows - 1, (
        f"Clicking a sending-table row must remove it; "
        f"was {initial_rows}, now {dialog.table_of_sending.rowCount()}"
    )
    assert dialog.add_name.text() == expected_key, (
        f"add_name must show the removed row's key; "
        f"got {dialog.add_name.text()!r}, expected {expected_key!r}"
    )


# ---------------------------------------------------------------------------
# _upload_env dispatch tests (ServerForm ↔ CompileEnvDialog integration)
# ---------------------------------------------------------------------------


def test_upload_env_calls_api_after_dialog_confirms(monkeypatch, qtbot, main, mock_api):
    """
    ServerForm._upload_env() must call api.upload_env() with the project name
    and the JSON payload built by CompileEnvDialog.do_upload().

    CompileEnvDialog is replaced by a stub whose show_dialog() immediately sets
    config_str (simulating the user clicking 'Update server' and closing the
    dialog) without blocking on exec().  This proves _upload_env() correctly
    reads config_str after the dialog returns and passes it to api.upload_env().
    """
    form = _open_server_form(main)
    _wire_mock(form, mock_api)

    stub_env_json = '{"STUB_VAR": "stub-value"}'

    class _StubEnvDialog:
        def __init__(self, *, parent, main, name):
            self.config_str = stub_env_json

        def show_dialog(self):
            pass  # do not enter exec() modal loop

    monkeypatch.setattr(
        "flightpath.widgets.config_forms.server_form.CompileEnvDialog",
        _StubEnvDialog,
    )

    form._upload_env("test-proj")

    mock_api.upload_env.assert_called_once()
    call_name = mock_api.upload_env.call_args[0][0]
    assert call_name == "test-proj", (
        f"upload_env must be called with 'test-proj'; got {call_name!r}"
    )
    env_data = json.loads(mock_api.upload_env.call_args[0][1])
    assert env_data.get("STUB_VAR") == "stub-value", (
        f"upload_env must receive the compiled JSON; got {mock_api.upload_env.call_args[0][1]!r}"
    )


def test_upload_env_skips_api_when_dialog_cancelled(monkeypatch, qtbot, main, mock_api):
    """
    When the user cancels CompileEnvDialog (config_str remains None),
    _upload_env() must not call api.upload_env() and must return False.

    The stub simulates the user clicking Cancel — show_dialog() returns without
    setting config_str, leaving it as None.
    """
    form = _open_server_form(main)
    _wire_mock(form, mock_api)

    class _StubEnvDialogCancelled:
        def __init__(self, *, parent, main, name):
            self.config_str = None  # user cancelled

        def show_dialog(self):
            pass

    monkeypatch.setattr(
        "flightpath.widgets.config_forms.server_form.CompileEnvDialog",
        _StubEnvDialogCancelled,
    )

    result = form._upload_env("test-proj")

    mock_api.upload_env.assert_not_called()
    assert result is False, (
        "upload_env must return False when the dialog is cancelled"
    )
