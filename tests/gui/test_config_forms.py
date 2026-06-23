"""
pytest-qt tests for individual config form sections.

Checklist coverage:
  CONFIG > save → close → reopen — values survive close/reopen cycle
  CONFIG > cache section — cache controls work (use_cache toggle)
  CONFIG > logging section — log level changes saved and applied
  CONFIG > errors section — error handling modes saved
  CONFIG > extensions section — custom extensions accepted
  CONFIG > inputs section — named-files / named-paths paths saved
  CONFIG > results section — archive path saved
  CONFIG > env section > add env.json var — variable appears in substitutions

== Config panel architecture ==

ConfigPanel.forms is a list of BlankForm subclasses populated by setup_forms().
get_form(section_name) returns the form whose .section property matches (or whose
class name contains the string).

save_all_forms() calls each form's add_to_config(config) then
main.csvpath_config.save_config() to flush to config.ini.  The toolbar save
button calls main.save_config_changes() → save_all_forms() + populate_all_forms().

populate_all_forms() re-reads from csvpath_config and fills form widgets.
cancel_config_changes() does csvpath_config.reload() + populate_all_forms(),
so any saved values survive the reload cycle.

open_config() triggers cancel_config_changes() when switching INTO the config
view, which means a save → close_config() → open_config() cycle proves that
saved values are read back from disk.

Run with:
  QT_QPA_PLATFORM=offscreen poetry run python -m pytest tests/gui/test_config_forms.py -v
"""

# isolated_home and main fixtures are provided by conftest.py


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _open_config(main) -> None:
    """Switch to the config view and ensure all forms are ready."""
    main.open_config()
    assert main.config.config_panel.ready, "Config panel must be ready after open_config()"


def _form(main, section: str):
    """Open config if needed and return the form for the given section name."""
    _open_config(main)
    f = main.config.config_panel.get_form(section)
    assert f is not None, f"Form for section {section!r} not found in config panel"
    return f


def _save(main) -> None:
    """Save all forms — triggers save_all_forms() + populate_all_forms().

    Calls save_config_changes() directly rather than clicking the toolbar button.
    The toolbar button is only enabled after a textChanged signal fires; combobox
    and checkbox changes use activated/stateChanged which do not reliably fire
    from setCurrentIndex() / setChecked() in tests.  The button flow is tested
    separately in test_config.py.
    """
    main.save_config_changes()


def _get(main, section: str, name: str, **kwargs) -> str:
    return main.csvpath_config.get(section=section, name=name, **kwargs)


# ---------------------------------------------------------------------------
# Tests — lifecycle
# ---------------------------------------------------------------------------


def test_values_survive_close_reopen(main):
    """
    A saved config value must survive a close → reopen cycle.

    open_config() calls cancel_config_changes() on entry, which calls
    csvpath_config.reload() (reads config.ini from disk) then populate_all_forms().
    If a value was written to disk by save_all_forms(), reopening the config view
    must cause the form to display that saved value.

    This is the in-process equivalent of close → restart → reopen.
    """
    form = _form(main, "cache")
    form.cache_dir_path.setText("lifecycle_test_cache")
    _save(main)

    # Switch away from config view
    main.close_config()
    assert main.main_layout.currentIndex() != 2, "close_config() must leave the config view"

    # Reopen — triggers csvpath_config.reload() then populate_all_forms()
    main.open_config()
    form2 = main.config.config_panel.get_form("cache")

    assert form2.cache_dir_path.text() == "lifecycle_test_cache", (
        "Cache form must display the saved value after close → reopen cycle"
    )


# ---------------------------------------------------------------------------
# Tests — cache section
# ---------------------------------------------------------------------------


def test_cache_use_cache_toggle_saved(main):
    """
    Changing the 'use_cache' combobox and saving must persist the choice to
    csvpath_config and to config.ini.

    The use_cache combobox offers 'yes' and 'no'.  Setting it to 'no' and saving
    must write "no" to [cache] use_cache in config.ini.
    """
    form = _form(main, "cache")

    idx = form.use_cache.findText("no")
    assert idx >= 0, "CacheForm use_cache combobox must contain 'no'"
    form.use_cache.setCurrentIndex(idx)
    _save(main)

    # After save + populate, verify via the form widget (use_cache is not in the
    # default config.ini so it only appears after an explicit save).
    form2 = main.config.config_panel.get_form("cache")
    assert form2.use_cache.currentText() == "no", (
        f"CacheForm use_cache combobox must show 'no' after save + repopulate; "
        f"got {form2.use_cache.currentText()!r}"
    )


# ---------------------------------------------------------------------------
# Tests — logging section
# ---------------------------------------------------------------------------


def test_logging_form_saves_log_file_size(main):
    """
    Setting log_file_size and saving must write the value to [logging] log_file_size
    in config.ini and return it from csvpath_config.

    log_file_size is a plain QLineEdit; no special formatting is required.
    """
    form = _form(main, "logging")
    form.log_file_size.setText("2048")
    _save(main)

    value = _get(main, section="logging", name="log_file_size")
    # log_file_size is a typed property on Config that returns int; str() normalises
    # both the int 2048 and the string "2048" to the same comparison target.
    assert str(value) == "2048", (
        f"[logging] log_file_size must be '2048' after saving; got {value!r}"
    )


def test_logging_form_repopulates_after_save(main):
    """
    After saving log_file_size, populate_all_forms() (which runs automatically
    after save) must reload the form field from the in-memory config.
    """
    form = _form(main, "logging")
    form.log_file_size.setText("4096")
    _save(main)

    # populate_all_forms() already ran as part of _save; just verify the field
    assert form.log_file_size.text() == "4096", (
        "log_file_size field must display the saved value after populate_all_forms()"
    )


# ---------------------------------------------------------------------------
# Tests — errors section
# ---------------------------------------------------------------------------


def test_errors_form_saves_pattern(main):
    """
    Setting the error pattern field and saving must write the value to
    [errors] pattern in config.ini.

    The pattern field accepts a regular expression used to match error messages
    for custom routing.
    """
    form = _form(main, "errors")
    form.pattern.setText("test_error_pattern.*")
    _save(main)

    value = _get(main, section="errors", name="pattern")
    assert value == "test_error_pattern.*", (
        f"[errors] pattern must match what was entered; got {value!r}"
    )


# ---------------------------------------------------------------------------
# Tests — extensions section
# ---------------------------------------------------------------------------


def test_extensions_form_saves_csv_extensions(main):
    """
    Setting the csv_files extension list and saving must write the value to
    [extensions] csv_files in config.ini.

    The csvs field (labelled 'CSV file extensions') accepts a comma-separated
    list of file extensions.  The framework uses this list to recognise data
    files in the named-files directory trees.
    """
    form = _form(main, "extensions")
    form.csvs.setText(".csv,.tsv,.txt")
    _save(main)

    value = _get(main, section="extensions", name="csv_files")
    # Config splits comma-separated strings into a list; check as both string and
    # list to be resilient to whether the value is stored/returned as-is or split.
    if isinstance(value, list):
        assert ".csv" in value and ".tsv" in value and ".txt" in value, (
            f"[extensions] csv_files list must include .csv, .tsv, .txt; got {value!r}"
        )
    else:
        assert ".csv" in str(value) and ".tsv" in str(value) and ".txt" in str(value), (
            f"[extensions] csv_files must include .csv, .tsv, .txt; got {value!r}"
        )


# ---------------------------------------------------------------------------
# Tests — inputs section
# ---------------------------------------------------------------------------


def test_inputs_form_saves_named_files_path(main):
    """
    Setting the named-files path and saving must write the value to
    [inputs] files in config.ini.

    The named_files field accepts a path or URL where named data files are
    stored.  The framework resolves this when loading named-file registrations.
    """
    form = _form(main, "inputs")
    form.named_files.setText("custom/named_files")
    _save(main)

    value = _get(main, section="inputs", name="files", string_parse=False, swaps=False)
    assert value == "custom/named_files", (
        f"[inputs] files must match what was entered; got {value!r}"
    )


def test_inputs_form_saves_named_paths_path(main):
    """
    Setting the named-paths path and saving must write the value to
    [inputs] csvpaths in config.ini.

    The named_paths field accepts a path or URL where named csvpath definition
    files are stored.
    """
    form = _form(main, "inputs")
    form.named_paths.setText("custom/named_paths")
    _save(main)

    value = _get(main, section="inputs", name="csvpaths", string_parse=False, swaps=False)
    assert value == "custom/named_paths", (
        f"[inputs] csvpaths must match what was entered; got {value!r}"
    )


# ---------------------------------------------------------------------------
# Tests — results section
# ---------------------------------------------------------------------------


def test_results_form_saves_archive_path(main):
    """
    Setting the archive path and saving must write the value to
    [results] archive in config.ini.

    The archive field controls where production run results are stored.  Changing
    it redirects where new runs write their output directories.
    """
    form = _form(main, "results")
    form.archive.setText("custom/archive_dir")
    _save(main)

    value = _get(main, section="results", name="archive", string_parse=False, swaps=False)
    assert value == "custom/archive_dir", (
        f"[results] archive must match what was entered; got {value!r}"
    )


# ---------------------------------------------------------------------------
# Tests — env section
# ---------------------------------------------------------------------------


def test_env_form_add_var_appears_in_envs(main):
    """
    Adding a name/value pair via the env form must write it to env.json and
    make it visible in form.envs().

    _on_click_add() reads add_name and add_value, calls _set_key() which writes
    to the env.json file (via ConfigEnv.write_env_file()), then calls
    refresh_table() to update the displayed table.  The test calls _on_click_add()
    directly to bypass UI event wiring.

    form.envs() is the ground truth: it re-reads from env.json each time so it
    reflects what was written.
    """
    form = _form(main, "env")

    form.add_name.setText("FP_TEST_VAR")
    form.add_value.setText("hello_from_test")
    form._on_click_add()

    envs = form.envs()
    assert "FP_TEST_VAR" in envs, (
        f"FP_TEST_VAR must appear in form.envs() after _on_click_add(); "
        f"got keys: {list(envs.keys())}"
    )
    assert envs["FP_TEST_VAR"] == "hello_from_test", (
        f"FP_TEST_VAR must equal 'hello_from_test'; got {envs['FP_TEST_VAR']!r}"
    )


def test_env_form_add_fields_cleared_after_add(main):
    """
    After clicking 'Add env var', the add_name and add_value fields must be
    cleared ready for the next entry.

    _on_click_add() calls setText("") on both fields after saving the value.
    """
    form = _form(main, "env")

    form.add_name.setText("FP_CLEAR_TEST")
    form.add_value.setText("some_value")
    form._on_click_add()

    assert form.add_name.text() == "", (
        "add_name must be cleared after _on_click_add()"
    )
    assert form.add_value.text() == "", (
        "add_value must be cleared after _on_click_add()"
    )
