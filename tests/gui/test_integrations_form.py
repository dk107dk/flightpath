"""
pytest-qt tests for ListenersForm (the "Integrations" tab) and all its sub-tabs.

Checklist coverage:
  CONFIG > integrations tab > select groups — group selections saved
  CONFIG > integrations tab > FTP setup — FTP connection fields saved
  (+ OTLP, OpenLineage, SQLite round-trip and db-creation integration test)

== ListenersForm structure ==

ListenersForm has:
  - groups (QLineEdit)     — comma-delimited active listener group names
  - my_tabs (QTabWidget)   — one tab per integration (sftp, otlp, openlineage,
                             sqlite, sql, slack, scripts, ckan)
  - scrollable label bar   — ClickableLabels that append a group name to the
                             groups field when clicked

Sub-tabs are accessed via form.tab_groups.get("<group_name>").

== OTLP special case ==

OtlpTab.add_to_config() writes directly to os.environ (not config.ini).
OtlpTab.populate() calls config.get(section=None, ...) which routes through
ConfigEnv: it reads from os.environ when var_sub_source=="env", otherwise from
env.json.  The populate test therefore temporarily sets var_sub_source="env".

== SQLite run integration test ==

Sqliter reads sqlite.db from main.csvpaths.config at run time.
main.csvpaths is a lazy property that caches a CsvPaths instance; its config
is initialized from disk at creation time.  To pick up config changes made via
main.csvpath_config we must:
  1. main.csvpath_config.save_config()  — write updated config to disk
  2. main.new_csvpaths()               — force a fresh CsvPaths that re-reads disk
After a successful run the sqlite listener creates the db file (and schema) on
first use inside SqliteResultsListener/SqliteResultListener.metadata_update().

Run with:
  QT_QPA_PLATFORM=offscreen poetry run python -m pytest tests/gui/test_integrations_form.py -v
"""

import os

import pytest

from csvpath.managers.files.files_activation_listener import FileActivationListener

# isolated_home and main fixtures provided by conftest.py

TIMEOUT = 30_000  # ms — production run + sqlite listener

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _form(main):
    main.open_config()
    form = main.config.config_panel.get_form("listeners")
    assert form is not None, "ListenersForm must be present in config panel"
    return form


def _tab(form, name: str):
    tab = form.tab_groups.get(name)
    assert tab is not None, f"Tab '{name}' must exist in ListenersForm tab_groups"
    return tab


def _examples(main, *parts) -> str:
    return os.path.join(main.state.cwd, "examples", *parts)


def _has_log_tab(tab_widget) -> bool:
    """Return True once a production-run Log tab (objectName 'Log-<cid>') exists."""
    for i in range(tab_widget.count()):
        if tab_widget.widget(i).objectName().startswith("Log-"):
            return True
    return False


# ---------------------------------------------------------------------------
# Groups field
# ---------------------------------------------------------------------------


def test_listeners_groups_saved_to_config(qtbot, main):
    """
    Setting groups and calling add_to_config() must persist the value to
    config["listeners"]["groups"].

    The groups field accepts comma-delimited listener group names.  The saved
    value is the raw text as entered.
    """
    form = _form(main)
    form.groups.setText("sftp, sqlite")
    form.add_to_config(main.csvpath_config)

    stored = main.csvpath_config.get(
        section="listeners", name="groups", string_parse=False, swaps=False
    )
    # config may return a list if it contains commas; normalise
    if isinstance(stored, list):
        stored = ", ".join(stored)
    assert "sftp" in stored, f"'sftp' must be in stored groups; got {stored!r}"
    assert "sqlite" in stored, f"'sqlite' must be in stored groups; got {stored!r}"


def test_listeners_groups_restored_on_populate(qtbot, main):
    """
    After writing groups to config and calling populate(), the groups field
    must display the stored value.
    """
    form = _form(main)
    main.csvpath_config.add_to_config("listeners", "groups", "sftp")

    form.populate()

    assert "sftp" in form.groups.text(), (
        f"groups field must show 'sftp' after populate(); got {form.groups.text()!r}"
    )


def test_listener_name_click_appends_group(qtbot, main):
    """
    Clicking a ClickableLabel in the group bar must append that group name to
    the groups field (comma-separated) if it is not already present.

    _listener_name_click() is called directly to avoid needing the real mouse
    event.
    """
    form = _form(main)
    form.groups.setText("")

    form._listener_name_click("otlp")

    assert "otlp" in form.groups.text(), (
        f"Clicking 'otlp' label must add it to groups; got {form.groups.text()!r}"
    )


def test_listener_name_click_does_not_duplicate(qtbot, main):
    """
    Clicking a label that is already in the groups field must not duplicate it.
    """
    form = _form(main)
    form.groups.setText("sftp")

    form._listener_name_click("sftp")

    # The text should still contain exactly one "sftp" (no duplication)
    assert form.groups.text().count("sftp") == 1, (
        f"'sftp' must not be duplicated; got {form.groups.text()!r}"
    )


# ---------------------------------------------------------------------------
# SFTP tab (FTP Setup — priority 1)
# ---------------------------------------------------------------------------


def test_sftp_all_fields_saved_to_config(qtbot, main):
    """
    Setting server, port, username, password and calling add_to_config() must
    write all four values to the [sftp] config section.

    This covers the checklist item 'FTP setup — FTP connection fields saved'.
    """
    form = _form(main)
    sftp = _tab(form, "sftp")

    sftp.server.setText("sftp.example.com")
    sftp.port.setText("22")
    sftp.username.setText("datauser")
    sftp.password.setText("s3cr3t")

    sftp.add_to_config(main.csvpath_config)

    cfg = main.csvpath_config
    assert cfg.get(section="sftp", name="server", string_parse=False, swaps=False) == "sftp.example.com"
    assert cfg.get(section="sftp", name="port", string_parse=False, swaps=False) == "22"
    assert cfg.get(section="sftp", name="username", string_parse=False, swaps=False) == "datauser"
    assert cfg.get(section="sftp", name="password", string_parse=False, swaps=False) == "s3cr3t"


def test_sftp_all_fields_restored_on_populate(qtbot, main):
    """
    After writing SFTP credentials to config, calling populate() must restore
    all four field values.
    """
    form = _form(main)
    sftp = _tab(form, "sftp")

    cfg = main.csvpath_config
    cfg.add_to_config("sftp", "server", "backup.example.com")
    cfg.add_to_config("sftp", "port", "2222")
    cfg.add_to_config("sftp", "username", "backup_user")
    cfg.add_to_config("sftp", "password", "backup_pass")

    sftp.populate()

    assert sftp.server.text() == "backup.example.com"
    assert sftp.port.text() == "2222"
    assert sftp.username.text() == "backup_user"
    assert sftp.password.text() == "backup_pass"


# ---------------------------------------------------------------------------
# OTLP tab (priority 2)
# ---------------------------------------------------------------------------


def test_otlp_fields_saved_to_os_environ(qtbot, main):
    """
    OtlpTab.add_to_config() must write endpoint and headers to os.environ.

    OTLP config does not go to config.ini; it is stored as OS env vars that
    OpenTelemetry SDKs read directly.
    """
    form = _form(main)
    otlp = _tab(form, "otlp")

    otlp.endpoint.setText("https://otlp.example.com:4317")
    otlp.headers.setText("Authorization=Bearer mytoken")

    otlp.add_to_config(main.csvpath_config)

    assert os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT") == "https://otlp.example.com:4317", (
        "OTEL_EXPORTER_OTLP_ENDPOINT must be set in os.environ after add_to_config()"
    )
    assert os.environ.get("OTEL_EXPORTER_OTLP_HEADERS") == "Authorization=Bearer mytoken", (
        "OTEL_EXPORTER_OTLP_HEADERS must be set in os.environ after add_to_config()"
    )


def test_otlp_populate_reads_from_os_environ(qtbot, main):
    """
    With var_sub_source set to 'env', populate() must read endpoint and headers
    from os.environ (ConfigEnv delegates to os.environ when source == 'env').
    """
    form = _form(main)
    otlp = _tab(form, "otlp")

    os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"] = "https://collector.internal:4318"
    os.environ["OTEL_EXPORTER_OTLP_HEADERS"] = "X-Api-Key=abc123"

    # Switch the env source so ConfigEnv reads from os.environ
    main.csvpath_config.add_to_config("config", "var_sub_source", "env")

    try:
        otlp.populate()
        assert otlp.endpoint.text() == "https://collector.internal:4318", (
            f"endpoint must be populated from os.environ; got {otlp.endpoint.text()!r}"
        )
        assert otlp.headers.text() == "X-Api-Key=abc123", (
            f"headers must be populated from os.environ; got {otlp.headers.text()!r}"
        )
    finally:
        del os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"]
        del os.environ["OTEL_EXPORTER_OTLP_HEADERS"]
        # restore default env source
        main.csvpath_config.add_to_config("config", "var_sub_source", "env.json")


# ---------------------------------------------------------------------------
# OpenLineage / Marquez tab (priority 3)
# ---------------------------------------------------------------------------


def test_openlineage_all_fields_saved_to_config(qtbot, main):
    """
    Setting all five OpenLineage fields and calling add_to_config() must write
    all to the [openlineage] config section.
    """
    form = _form(main)
    ol = _tab(form, "openlineage")

    ol.base_url.setText("http://marquez.example.com:5000")
    ol.endpoint.setText("api/v1/lineage")
    ol.api_key.setText("ol-secret-key")
    ol.timeout.setText("30")
    ol.verify.setText("true")

    ol.add_to_config(main.csvpath_config)

    cfg = main.csvpath_config
    assert cfg.get(section="openlineage", name="base_url", string_parse=False, swaps=False) == "http://marquez.example.com:5000"
    assert cfg.get(section="openlineage", name="endpoint", string_parse=False, swaps=False) == "api/v1/lineage"
    assert cfg.get(section="openlineage", name="api_key", string_parse=False, swaps=False) == "ol-secret-key"
    assert cfg.get(section="openlineage", name="timeout", string_parse=False, swaps=False) == "30"
    assert cfg.get(section="openlineage", name="verify", string_parse=False, swaps=False) == "true"


def test_openlineage_all_fields_restored_on_populate(qtbot, main):
    """
    After writing OpenLineage config values, calling populate() must restore
    all five fields.
    """
    form = _form(main)
    ol = _tab(form, "openlineage")

    cfg = main.csvpath_config
    cfg.add_to_config("openlineage", "base_url", "http://ol.internal:5000")
    cfg.add_to_config("openlineage", "endpoint", "api/v1/lineage")
    cfg.add_to_config("openlineage", "api_key", "key-abc")
    cfg.add_to_config("openlineage", "timeout", "15")
    cfg.add_to_config("openlineage", "verify", "false")

    ol.populate()

    assert ol.base_url.text() == "http://ol.internal:5000"
    assert ol.endpoint.text() == "api/v1/lineage"
    assert ol.api_key.text() == "key-abc"
    assert ol.timeout.text() == "15"
    assert ol.verify.text() == "false"


# ---------------------------------------------------------------------------
# SQLite tab — form tests (priority 4)
# ---------------------------------------------------------------------------


def test_sqlite_db_path_saved_to_config(qtbot, main):
    """
    Setting the database file path and calling add_to_config() must write the
    value to config["sqlite"]["db"].
    """
    form = _form(main)
    sq = _tab(form, "sqlite")

    sq.db.setText("/tmp/flightpath_test.db")
    sq.add_to_config(main.csvpath_config)

    stored = main.csvpath_config.get(
        section="sqlite", name="db", string_parse=False, swaps=False
    )
    assert stored == "/tmp/flightpath_test.db", (
        f'config["sqlite"]["db"] must be "/tmp/flightpath_test.db"; got {stored!r}'
    )


def test_sqlite_db_path_restored_on_populate(qtbot, main):
    """
    After writing a db path to config, calling populate() must restore the
    db field to that value.
    """
    form = _form(main)
    sq = _tab(form, "sqlite")

    main.csvpath_config.add_to_config("sqlite", "db", "/var/data/my.db")
    sq.populate()

    assert sq.db.text() == "/var/data/my.db", (
        f"db field must show the stored path after populate(); got {sq.db.text()!r}"
    )


# ---------------------------------------------------------------------------
# SQLite integration test — db file created after run
# ---------------------------------------------------------------------------


def test_sqlite_db_created_after_run(monkeypatch, qtbot, main, tmp_path):
    """
    A production run with listeners.groups = sqlite must create the SQLite
    database file at the path configured in sqlite.db.

    Flow:
      1. Configure sqlite.db and listeners.groups in main.csvpath_config and
         save to disk.
      2. Call main.new_csvpaths() so the CsvPaths instance re-reads the
         updated config from disk (main.csvpaths.config is otherwise frozen
         from the initial disk read at startup).
      3. Stage a named-file and load a named-paths group.
      4. Run via main.run_paths() and wait for the Log tab.
      5. Verify the db file exists; it is created by Sqliter in
         SqliteResultsListener/SqliteResultListener.metadata_update().

    FileActivationListener.metadata_update is suppressed to prevent the
    Lark-grammar background thread from racing Qt's proxy model.
    """
    monkeypatch.setattr(FileActivationListener, "metadata_update", lambda self, mdata: None)

    db_path = str(tmp_path / "csvpath_results.db")

    # 1. Configure sqlite listener and save to disk.
    #    run_paths() calls main.new_csvpaths() internally, so the CsvPaths
    #    instance used during the run reads the updated config from disk.
    main.csvpath_config.add_to_config("sqlite", "db", db_path)
    main.csvpath_config.add_to_config("listeners", "groups", "sqlite")
    main.csvpath_config.save_config()

    # 2. Register a named-file and named-paths group
    csv_file = _examples(main, "first steps", "test.csv")
    csvpath_file = _examples(main, "first steps", "Hello World.csvpath")

    assert os.path.exists(csv_file), f"Test CSV not found: {csv_file}"
    assert os.path.exists(csvpath_file), f"Test csvpath not found: {csvpath_file}"

    main.csvpaths.file_manager.add_named_file(
        name="test", path=csv_file, template=None
    )
    main.csvpaths.paths_manager.add_named_paths_from_file(
        name="hello-world", file_path=csvpath_file, template=None, append=False
    )

    # 4. Run and wait for the Log tab.
    #    run_paths() calls new_csvpaths() internally; that fresh instance reads
    #    the updated config from disk (sqlite.db and listeners.groups = sqlite).
    hf = main.helper.help_and_feedback
    main.run_paths(
        method="collect_paths",
        named_file_name="test",
        named_paths_name="hello-world",
        template=None,
    )

    qtbot.waitUntil(lambda: _has_log_tab(hf), timeout=TIMEOUT)

    # 5. Verify the SQLite db was created by the listener
    assert os.path.exists(db_path), (
        f"SQLite db must be created at {db_path!r} after a run with "
        f"listeners.groups=sqlite; file does not exist"
    )


# ---------------------------------------------------------------------------
# Slack tab (nice to have)
# ---------------------------------------------------------------------------


def test_slack_webhook_url_roundtrip(qtbot, main):
    """
    Setting a Slack webhook URL, saving to config, and calling populate() on
    a fresh tab must restore the URL.
    """
    form = _form(main)
    slack = _tab(form, "slack")

    slack.webhook_url.setText("https://hooks.slack.com/services/T000/B000/xxx")
    slack.add_to_config(main.csvpath_config)

    # Verify config has it
    stored = main.csvpath_config.get(
        section="slack", name="webhook_url", string_parse=False, swaps=False
    )
    assert stored == "https://hooks.slack.com/services/T000/B000/xxx"

    # Verify populate restores it
    slack.webhook_url.setText("")
    slack.populate()
    assert slack.webhook_url.text() == "https://hooks.slack.com/services/T000/B000/xxx"


# ---------------------------------------------------------------------------
# CKAN tab (lowest priority)
# ---------------------------------------------------------------------------


def test_ckan_fields_roundtrip(qtbot, main):
    """
    Setting CKAN server and api_token, saving, and repopulating must restore
    both values.
    """
    form = _form(main)
    ckan = _tab(form, "ckan")

    ckan.server.setText("https://data.example.gov")
    ckan.api_token.setText("tok-abc-123")
    ckan.add_to_config(main.csvpath_config)

    ckan.server.setText("")
    ckan.api_token.setText("")
    ckan.populate()

    assert ckan.server.text() == "https://data.example.gov"
    assert ckan.api_token.text() == "tok-abc-123"


# ---------------------------------------------------------------------------
# SQL tab (bonus — uses sqlite dialect to verify sql form works end-to-end)
# ---------------------------------------------------------------------------


def test_sql_tab_fields_roundtrip(qtbot, main):
    """
    Setting dialect and connection_string and calling add_to_config() must
    write both to [sql] config section; populate() must restore them.

    The sql tab is the generic SQL backend form.  Using a sqlite connection
    string keeps the test self-contained (no external server needed).
    """
    form = _form(main)
    sql = _tab(form, "sql")

    sql.dialect.setText("sqlite")
    sql.connection_string.setText("sqlite:///tmp/test_via_sql_tab.db")
    sql.add_to_config(main.csvpath_config)

    cfg = main.csvpath_config
    assert cfg.get(section="sql", name="dialect", string_parse=False, swaps=False) == "sqlite"
    assert cfg.get(section="sql", name="connection_string", string_parse=False, swaps=False) == "sqlite:///tmp/test_via_sql_tab.db"

    sql.dialect.setText("")
    sql.connection_string.setText("")
    sql.populate()

    assert sql.dialect.text() == "sqlite"
    assert sql.connection_string.text() == "sqlite:///tmp/test_via_sql_tab.db"
