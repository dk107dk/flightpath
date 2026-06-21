"""
pytest-qt tests for the config panel save/load workflow.

Checklist coverage: CONFIG > check save and load
  > actual value changes on save and reload
  > cache

Tests use the Cache form (forms_layout index 3) because it has a simple
text field (cache directory path) that maps directly to [cache] path in
config.ini, making both in-memory and on-disk verification straightforward.

Save cycle:  open config → change field → click 'Save and reload'
             → assert csvpath_config in memory AND config.ini on disk
               both reflect the new value.
Cancel cycle: open config → change field → click 'Revert changes'
              → assert field and csvpath_config restore the original value.

Run with:
  QT_QPA_PLATFORM=offscreen poetry run python -m pytest tests/gui/test_config.py -v
"""

import configparser
import os

# isolated_home and main fixtures are provided by conftest.py

NEW_CACHE_PATH = "test_cache_override"


def _open_config(main) -> None:
    """Switch to the config view and ensure all forms are populated."""
    main.open_config()
    assert main.config.config_panel.ready, "Config panel must be ready after open_config()"


def _cache_form(main):
    """Return the CacheForm; opens config first if needed."""
    _open_config(main)
    form = main.config.config_panel.get_form("cache")
    assert form is not None, "CacheForm not found in config panel"
    return form


# ========= TESTS ============


def test_open_config_switches_to_config_view(main):
    """
    open_config() must switch the main stacked layout to the config view
    (index 2) and mark the config panel ready.
    """
    assert main.main_layout.currentIndex() == 0

    main.open_config()

    assert main.main_layout.currentIndex() == 2
    assert main.config.config_panel.ready
    assert main.config.config_panel.forms is not None
    assert len(main.config.config_panel.forms) > 0


def test_save_config_persists_value_to_ini(main):
    """
    Changing the cache-directory field and clicking 'Save and reload' must
    update csvpath_config in memory and write the new value to config.ini.
    """
    form = _cache_form(main)
    form.cache_dir_path.setText(NEW_CACHE_PATH)

    main.config.toolbar._button_save.click()

    assert main.csvpath_config.get(section="cache", name="path") == NEW_CACHE_PATH

    config_ini_path = os.path.join(main.state.cwd, "config", "config.ini")
    parser = configparser.ConfigParser()
    parser.read(config_ini_path)
    assert parser.get("cache", "path") == NEW_CACHE_PATH


def test_save_config_repopulates_form(main):
    """
    After 'Save and reload', populate_all_forms() runs and the cache form
    must display the saved value without further interaction.
    """
    form = _cache_form(main)
    form.cache_dir_path.setText(NEW_CACHE_PATH)

    main.config.toolbar._button_save.click()

    assert form.cache_dir_path.text() == NEW_CACHE_PATH


def test_cancel_config_reverts_value(main):
    """
    Changing a field then clicking 'Revert changes' must restore the
    original value in both the form widget and csvpath_config in memory.
    """
    form = _cache_form(main)
    original = main.csvpath_config.get(
        section="cache", name="path", default="cache"
    )

    form.cache_dir_path.setText(NEW_CACHE_PATH)
    assert form.cache_dir_path.text() == NEW_CACHE_PATH
    assert main.config.toolbar.button_cancel_changes.isEnabled(), (
        "Cancel button must become enabled after a field change"
    )

    main.config.toolbar.button_cancel_changes.click()

    assert form.cache_dir_path.text() == original
    assert (
        main.csvpath_config.get(section="cache", name="path", default="cache")
        == original
    )
