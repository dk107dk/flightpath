"""
pytest-qt tests for EnvForm and the env-related ConfigForm behaviour.

Checklist coverage:
  CONFIG > env section > env.json var sub visible in actuals panel
  CONFIG > env section > switch env.json → env — actuals shows no substitution available
  CONFIG > env section > switch back to env.json — full path auto-populated

== EnvForm overview ==

EnvForm displays env vars in a QTableWidget (env_table) with two columns:
  col 0 — Name  (read-only)
  col 1 — Value (editable)

The source of vars is determined by config["config"]["var_sub_source"]:
  "env"         → reads os.environ (potentially hundreds of rows)
  <json path>   → reads the env.json file for the project (few rows)

  _on_click_add()       — adds/deletes a var and calls refresh_table()
  refresh_table()       — rebuilds env_table from the current source
  _on_click_update()    — re-applies the filter and calls refresh_table()

The filter_input QLineEdit accepts a regex; only vars whose names match are shown.

== ConfigForm.var_sub_source auto-completion ==

When the user enters a partial filename (e.g. "myenv") into var_sub_source and
saves, ConfigForm.add_to_config() calls assure_env_path() which:
  - appends ".json" if the path doesn't end with it
  - creates the file if it doesn't exist
  - sets var_sub_source.setText(full_absolute_path)

This covers the "switch back to env.json — full path auto-populated" checklist item.

Run with:
  QT_QPA_PLATFORM=offscreen poetry run python -m pytest tests/gui/test_env_form.py -v
"""

import os

# isolated_home and main fixtures provided by conftest.py


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _env_form(main):
    main.open_config()
    form = main.config.config_panel.get_form("EnvForm")
    assert form is not None, "EnvForm must be present in config panel"
    return form


def _config_form(main):
    main.open_config()
    # get_form("config") matches every form because all live in the config_forms
    # module and "config" appears in every type string. Use the full class name.
    form = main.config.config_panel.get_form("ConfigForm")
    assert form is not None, "ConfigForm must be present in config panel"
    return form


def _table_names(form) -> list[str]:
    """Return all Name column values from env_table."""
    return [
        form.env_table.item(row, 0).text()
        for row in range(form.env_table.rowCount())
        if form.env_table.item(row, 0) is not None
    ]


# ---------------------------------------------------------------------------
# EnvForm — env.json source (default)
# ---------------------------------------------------------------------------


def test_env_form_add_var_appears_in_table(qtbot, main):
    """
    Adding a var via _on_click_add() must make it visible in env_table.

    env_table is the 'actuals panel' for the env section.  After adding a var
    its name must appear in the Name column.
    """
    form = _env_form(main)

    # Ensure source is env.json (default for new projects)
    assert not form._os(), (
        "New project must default to env.json source, not os.environ"
    )

    form.add_name.setText("FP_TEST_KEY")
    form.add_value.setText("hello_from_test")
    form._on_click_add()

    names = _table_names(form)
    assert "FP_TEST_KEY" in names, (
        f"env_table must contain FP_TEST_KEY after adding it; got names={names!r}"
    )


def test_env_form_added_var_value_is_correct(qtbot, main):
    """
    The Value column for a newly added var must match the value entered.
    """
    form = _env_form(main)

    form.add_name.setText("FP_VAL_TEST")
    form.add_value.setText("testvalue42")
    form._on_click_add()

    for row in range(form.env_table.rowCount()):
        name_item = form.env_table.item(row, 0)
        if name_item and name_item.text() == "FP_VAL_TEST":
            val_item = form.env_table.item(row, 1)
            assert val_item is not None, "Value item must exist for FP_VAL_TEST"
            assert val_item.text() == "testvalue42", (
                f"Value must be 'testvalue42'; got {val_item.text()!r}"
            )
            return
    raise AssertionError("FP_VAL_TEST not found in env_table after add")


def test_env_form_filter_limits_displayed_vars(qtbot, main):
    """
    Entering a regex in filter_input and clicking 'Update filter' must limit
    env_table to only matching var names.

    Two vars are added with distinct prefixes; the filter is set to match only
    one prefix.  The other var must not appear in the table.
    """
    form = _env_form(main)

    form.add_name.setText("ALPHA_KEY")
    form.add_value.setText("aaa")
    form._on_click_add()

    form.add_name.setText("BETA_KEY")
    form.add_value.setText("bbb")
    form._on_click_add()

    form.filter_input.setText("^ALPHA")
    form._on_click_update()

    names = _table_names(form)
    assert "ALPHA_KEY" in names, "ALPHA_KEY must appear when filter matches it"
    assert "BETA_KEY" not in names, (
        "BETA_KEY must not appear when filter excludes it"
    )


def test_env_form_empty_filter_shows_all_vars(qtbot, main):
    """
    Clearing filter_input and updating must restore all vars to env_table.
    """
    form = _env_form(main)

    form.add_name.setText("GAMMA_KEY")
    form.add_value.setText("ggg")
    form._on_click_add()

    form.add_name.setText("DELTA_KEY")
    form.add_value.setText("ddd")
    form._on_click_add()

    form.filter_input.setText("^GAMMA")
    form._on_click_update()
    names_filtered = _table_names(form)
    assert "DELTA_KEY" not in names_filtered

    form.filter_input.setText("")
    form._on_click_update()
    names_all = _table_names(form)
    assert "GAMMA_KEY" in names_all, "GAMMA_KEY must reappear after clearing filter"
    assert "DELTA_KEY" in names_all, "DELTA_KEY must reappear after clearing filter"


def test_env_form_delete_var_by_empty_value(qtbot, main):
    """
    Adding a var then re-adding it with an empty value must delete it from
    env_table.

    _on_click_add() calls _delete_key(name) when value is empty or whitespace.
    """
    form = _env_form(main)

    form.add_name.setText("EPHEMERAL_KEY")
    form.add_value.setText("exists")
    form._on_click_add()
    assert "EPHEMERAL_KEY" in _table_names(form), "Precondition: key must exist"

    form.add_name.setText("EPHEMERAL_KEY")
    form.add_value.setText("")
    form._on_click_add()

    assert "EPHEMERAL_KEY" not in _table_names(form), (
        "EPHEMERAL_KEY must be removed from env_table after setting empty value"
    )


# ---------------------------------------------------------------------------
# EnvForm — switch to OS env source
# ---------------------------------------------------------------------------


def test_env_form_os_source_shows_os_environ_vars(monkeypatch, qtbot, main):
    """
    When var_sub_source is set to 'env', env_table must show variables from
    os.environ rather than env.json.

    The test patches the config value via main.csvpath_config to avoid a full
    config save cycle.  It then verifies that env_table shows at least one of
    the expected OS env vars (PATH or HOME, which are present in all POSIX
    environments including offscreen CI).

    This covers 'switch env.json → env — actuals shows OS env vars'.
    """
    form = _env_form(main)

    # Confirm default is env.json
    assert not form._os(), "Precondition: must be on env.json source"

    # Switch to OS env by patching config directly
    main.csvpath_config.add_to_config("config", "var_sub_source", "env")
    assert form._os(), "_os() must return True after setting var_sub_source='env'"

    form.refresh_table()

    names = _table_names(form)
    os_env_keys = set(os.environ.keys())
    overlap = set(names) & os_env_keys
    assert len(overlap) > 0, (
        "env_table must show at least one OS env var when source is 'env'; "
        f"got table names={names[:5]!r}..."
    )


# ---------------------------------------------------------------------------
# ConfigForm — var_sub_source auto-completion
# ---------------------------------------------------------------------------


def test_config_form_var_sub_source_auto_completes_to_json(qtbot, main):
    """
    Entering a bare filename (without .json) in var_sub_source and calling
    add_to_config() must auto-complete it to a full absolute .json path.

    ConfigForm.add_to_config() calls assure_env_path() which appends '.json'
    and creates the file, then updates var_sub_source with the full path.

    This covers 'switch back to env.json — full path auto-populated'.
    """
    config_form = _config_form(main)

    # Provide a bare name — no .json extension, no leading path
    config_form.var_sub_source.setText("myenv")
    config_form.add_to_config(main.csvpath_config)

    actual = config_form.var_sub_source.text()
    assert actual.endswith(".json"), (
        f"var_sub_source must end with '.json' after auto-completion; got {actual!r}"
    )
    assert os.path.isabs(actual), (
        f"var_sub_source must be an absolute path after auto-completion; got {actual!r}"
    )
    assert os.path.exists(actual), (
        f"assure_env_path() must create the env file at {actual!r}"
    )


def test_config_form_var_sub_source_env_string_preserved(qtbot, main):
    """
    When var_sub_source is explicitly set to 'env', add_to_config() must
    preserve the literal string 'env' and not expand it to a file path.

    'env' is the sentinel that tells EnvForm._os() to use os.environ.
    """
    config_form = _config_form(main)
    config_form.var_sub_source.setText("env")
    config_form.add_to_config(main.csvpath_config)

    stored = main.csvpath_config.get(
        section="config", name="var_sub_source", string_parse=False, swaps=False
    )
    assert stored == "env", (
        f"var_sub_source must remain 'env' when set explicitly; got {stored!r}"
    )
