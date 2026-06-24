"""
pytest-qt tests for the Welcome page buttons.

Checklist coverage: HOME > welcome buttons don't blow up

Five buttons are tested:
  - "Trigger a run"    disabled in an empty project (no named files/paths)
  - "Find data"        disabled in an empty project (no named files or results)
  - "Configure AI"     switches to Config view (stacked index 2) with LLM form (form index 13)
  - "Reload Ops Files" rebuilds the UI and leaves the window on Welcome (index 0)
  - "Copy data in"     calls os.system with the project cwd; no native dialog opened

Run with:
  QT_QPA_PLATFORM=offscreen poetry run python -m pytest tests/gui/test_welcome_buttons.py -v
"""

import os

# isolated_home and main fixtures are provided by conftest.py


# ========= TESTS ============

#chked
def test_run_button_disabled_in_empty_project(main):
    """
    A fresh project has no named files or paths registered, so 'Trigger a run'
    must be disabled — there is nothing to run against.
    """
    assert not main.welcome.button_run.isEnabled()

#chked
def test_find_data_button_disabled_in_empty_project(main):
    """
    A fresh project has no named files and no archived results, so 'Find data'
    must be disabled — there is nothing to find.
    """
    assert not main.welcome.button_find_data.isEnabled()

#chked
def test_configure_ai_button_switches_to_config(main):
    """
    Clicking 'Configure AI' must navigate to the Config view (stacked layout
    index 2) and select the LLM form (forms_layout index 13).
    """
    assert main.main_layout.currentIndex() == 0

    main.welcome.button_ai.click()

    assert main.main_layout.currentIndex() == 2
    assert main.config.config_panel.forms_layout.currentIndex() == 13

#chked
def test_reload_button_stays_on_welcome(qtbot, main):
    """
    Clicking 'Reload Ops Files' tears down and rebuilds the central widget tree.
    Afterwards the window must still be on the Welcome page (stacked index 0)
    with all key widget attributes repopulated.
    """
    assert main.main_layout.currentIndex() == 0

    main.welcome.button_reload.click()

    qtbot.waitUntil(lambda: main.main_layout.currentIndex() == 0, timeout=3000)
    assert main.welcome is not None
    assert main.content is not None
    assert main.sidebar is not None

#chked
def test_copy_in_button_opens_project_dir(main, monkeypatch):
    """
    'Copy data in' must call os.system with the current project directory.
    We monkeypatch os.system to intercept the call so no native Finder/Explorer
    window opens during the test run.
    """
    calls = []
    monkeypatch.setattr(os, "system", lambda cmd: calls.append(cmd))

    expected_cwd = main.state.cwd
    main.welcome.button_copy_in.click()

    assert len(calls) == 1
    assert expected_cwd in calls[0]
