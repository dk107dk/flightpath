"""
pytest-qt tests for LlmForm (the "LLM / AI section" config form).

Checklist coverage:
  CONFIG > LLM / AI section > generator.ini path displayed correctly
  CONFIG > LLM / AI section > "use for all projects" — setting propagates
  CONFIG > LLM / AI section > open metadata dir — button doesn't crash
  CONFIG > LLM / AI section > open generator.ini — button doesn't crash

== LlmForm overview ==

LlmForm has three editable fields and one checkbox:
  model          QLineEdit  → config["llm"]["model"]
  base           QLineEdit  → config["llm"]["api_base"]
  key            QLineEdit  → config["llm"]["api_key"]
  checkbox       QCheckBox  → "Use for all projects"

add_to_config() always writes the three fields to config["llm"].  When the
checkbox is checked it also writes to main.state.data["llm"] — the JSON state
file that persists across projects.

populate() reads from config["llm"] first; if any value is missing there, it
falls back to main.state.data["llm"].  If state was used, populate() saves
the state values to config["llm"] automatically so future reads hit config.

The checkbox is set by _llm_config_matches_state(): True when config["llm"]
and state["llm"] hold the same non-empty values.

ai_config_path (QLabel) shows the path to the project's generator.ini — the
FlightPath Generator config file, located in the same directory as config.ini.

The actuals table (from BlankForm, fields = ["model", "api_base", "api_key"])
shows the current resolved values from config.

Run with:
  QT_QPA_PLATFORM=offscreen poetry run python -m pytest tests/gui/test_llm_form.py -v
"""

import os

from flightpath.util.os_utility import OsUtility as osut

# isolated_home and main fixtures provided by conftest.py


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _form(main):
    main.open_config()
    form = main.config.config_panel.get_form("llm")
    assert form is not None, "LlmForm must be present in config panel"
    return form


# ---------------------------------------------------------------------------
# Field save / restore
# ---------------------------------------------------------------------------


def test_llm_fields_saved_to_config(qtbot, main):
    """
    Setting model, base, and key and calling add_to_config() must write all
    three values to config["llm"].
    """
    form = _form(main)
    form.model.setText("gpt-4o")
    form.base.setText("https://api.openai.com/v1")
    form.key.setText("sk-test-1234")

    form.add_to_config(main.csvpath_config)

    cfg = main.csvpath_config
    assert cfg.get(section="llm", name="model", string_parse=False, swaps=False) == "gpt-4o"
    assert cfg.get(section="llm", name="api_base", string_parse=False, swaps=False) == "https://api.openai.com/v1"
    assert cfg.get(section="llm", name="api_key", string_parse=False, swaps=False) == "sk-test-1234"


def test_llm_fields_restored_on_populate_from_config(qtbot, main):
    """
    After writing LLM values to config and calling populate(), all three fields
    must display the stored values.
    """
    form = _form(main)
    cfg = main.csvpath_config
    cfg.add_to_config("llm", "model", "claude-sonnet-4-6")
    cfg.add_to_config("llm", "api_base", "https://api.anthropic.com")
    cfg.add_to_config("llm", "api_key", "ant-key-abc")

    form.populate()

    assert form.model.text() == "claude-sonnet-4-6"
    assert form.base.text() == "https://api.anthropic.com"
    assert form.key.text() == "ant-key-abc"


def test_llm_fields_strip_whitespace_on_save(qtbot, main):
    """
    add_to_config() calls .strip() on each field value before writing to
    config.  Leading/trailing whitespace must not be stored.
    """
    form = _form(main)
    form.model.setText("  gpt-4  ")
    form.base.setText("  https://api.openai.com/v1  ")
    form.key.setText("  sk-abc  ")

    form.add_to_config(main.csvpath_config)

    cfg = main.csvpath_config
    assert cfg.get(section="llm", name="model", string_parse=False, swaps=False) == "gpt-4"
    assert cfg.get(section="llm", name="api_base", string_parse=False, swaps=False) == "https://api.openai.com/v1"
    assert cfg.get(section="llm", name="api_key", string_parse=False, swaps=False) == "sk-abc"


# ---------------------------------------------------------------------------
# "Use for all projects" checkbox
# ---------------------------------------------------------------------------


def test_llm_checkbox_checked_writes_to_state(qtbot, main):
    """
    With the checkbox checked, add_to_config() must write the three LLM values
    to main.state.data["llm"].

    main.state.data is the .flightpath JSON file that is shared across all
    projects — the mechanism behind "use for all projects".
    """
    form = _form(main)
    form.model.setText("gpt-4o")
    form.base.setText("https://api.openai.com/v1")
    form.key.setText("sk-global")
    form.checkbox.setChecked(True)

    form.add_to_config(main.csvpath_config)

    ai = main.state.data.get("llm", {})
    assert ai.get("model") == "gpt-4o", (
        f"state.data['llm']['model'] must be 'gpt-4o'; got {ai.get('model')!r}"
    )
    assert ai.get("api_base") == "https://api.openai.com/v1"
    assert ai.get("api_key") == "sk-global"


def test_llm_checkbox_unchecked_does_not_write_to_state(qtbot, main):
    """
    With the checkbox unchecked, add_to_config() must NOT write to
    main.state.data["llm"].

    The state starts empty in the isolated test environment, so if no state
    write occurs, state.data.get("llm") remains None.
    """
    form = _form(main)
    form.model.setText("gpt-4o")
    form.base.setText("https://api.openai.com/v1")
    form.key.setText("sk-local-only")
    form.checkbox.setChecked(False)

    form.add_to_config(main.csvpath_config)

    ai = main.state.data.get("llm")
    assert ai is None or ai.get("api_key") != "sk-local-only", (
        "state.data['llm'] must not be updated when 'use for all projects' is unchecked"
    )


def test_llm_populate_falls_back_to_state_when_config_empty(qtbot, main):
    """
    When config["llm"] is empty, populate() must read from main.state.data["llm"]
    and display those values in the fields.

    This is the 'use for all projects' read path: a project with no LLM config
    inherits the values saved in the shared state by another project.
    """
    form = _form(main)

    # Write values to state directly (simulating another project having saved them)
    data = main.state.data
    data["llm"] = {
        "model": "claude-haiku-4-5",
        "api_base": "https://api.anthropic.com",
        "api_key": "sk-state-fallback",
    }
    main.state.data = data

    # Ensure config is empty so populate falls back to state
    main.csvpath_config.add_to_config("llm", "model", "")
    main.csvpath_config.add_to_config("llm", "api_base", "")
    main.csvpath_config.add_to_config("llm", "api_key", "")

    form.populate()

    assert form.model.text() == "claude-haiku-4-5", (
        f"model field must fall back to state value; got {form.model.text()!r}"
    )
    assert form.base.text() == "https://api.anthropic.com"
    assert form.key.text() == "sk-state-fallback"


def test_llm_checkbox_checked_when_config_matches_state(qtbot, main):
    """
    The checkbox must be checked when config["llm"] and state["llm"] hold the
    same non-empty values (_llm_config_matches_state() returns True).
    """
    form = _form(main)

    cfg = main.csvpath_config
    cfg.add_to_config("llm", "model", "gpt-4o")
    cfg.add_to_config("llm", "api_base", "https://api.openai.com/v1")
    cfg.add_to_config("llm", "api_key", "sk-match")

    data = main.state.data
    data["llm"] = {"model": "gpt-4o", "api_base": "https://api.openai.com/v1", "api_key": "sk-match"}
    main.state.data = data

    form.populate()

    assert form.checkbox.isChecked(), (
        "Checkbox must be checked when config and state hold the same LLM values"
    )


def test_llm_checkbox_unchecked_when_config_differs_from_state(qtbot, main):
    """
    The checkbox must be unchecked when config["llm"] and state["llm"] differ
    (_llm_config_matches_state() returns False).
    """
    form = _form(main)

    cfg = main.csvpath_config
    cfg.add_to_config("llm", "model", "gpt-4o")
    cfg.add_to_config("llm", "api_base", "https://api.openai.com/v1")
    cfg.add_to_config("llm", "api_key", "sk-config")

    data = main.state.data
    data["llm"] = {"model": "claude-sonnet-4-6", "api_base": "https://api.anthropic.com", "api_key": "sk-state"}
    main.state.data = data

    form.populate()

    assert not form.checkbox.isChecked(), (
        "Checkbox must be unchecked when config and state hold different LLM values"
    )


# ---------------------------------------------------------------------------
# generator.ini path display
# ---------------------------------------------------------------------------


def test_llm_generator_ini_path_displayed(qtbot, main):
    """
    The ai_config_path QLabel must display a path that ends with 'generator.ini'.

    _generator_config_path() derives this from config["config"]["path"] (the
    config.ini location): it takes the parent directory and appends
    'generator.ini'.  This path is set in __init__ and does not depend on the
    generator being present on disk.
    """
    form = _form(main)
    label_text = form.ai_config_path.text()

    assert label_text.endswith("generator.ini"), (
        f"ai_config_path label must end with 'generator.ini'; got {label_text!r}"
    )
    assert os.path.isabs(label_text), (
        f"ai_config_path label must be an absolute path; got {label_text!r}"
    )


def test_llm_generator_ini_path_in_config_dir(qtbot, main):
    """
    The generator.ini path must live in the same directory as config.ini.

    This ensures generator config is found relative to the project's config
    directory, not an arbitrary location.
    """
    form = _form(main)
    label_path = form.ai_config_path.text()

    config_ini_path = main.csvpath_config.configpath
    config_dir = os.path.dirname(config_ini_path)

    assert os.path.dirname(label_path) == config_dir, (
        f"generator.ini must be in config dir {config_dir!r}; "
        f"label shows {label_path!r}"
    )


# ---------------------------------------------------------------------------
# Actuals table
# ---------------------------------------------------------------------------


def test_llm_actuals_table_shows_all_three_fields(qtbot, main):
    """
    After add_to_config() and update_table(), the actuals table must show rows
    for 'model', 'api_base', and 'api_key' — the three keys in LlmForm.fields.
    """
    form = _form(main)
    form.model.setText("gpt-4o")
    form.base.setText("https://api.openai.com/v1")
    form.key.setText("sk-test")
    form.add_to_config(main.csvpath_config)
    form.update_table()

    assert form.table is not None, "LlmForm must have an actuals table"
    assert form.table.rowCount() == 3, (
        f"Actuals table must have 3 rows (model, api_base, api_key); "
        f"got {form.table.rowCount()}"
    )

    names = {form.table.item(r, 0).text() for r in range(3) if form.table.item(r, 0)}
    assert "model" in names
    assert "api_base" in names
    assert "api_key" in names


def test_llm_actuals_table_shows_saved_model_value(qtbot, main):
    """
    After saving a model value, the actuals table must show that value in the
    row corresponding to 'model'.
    """
    form = _form(main)
    form.model.setText("claude-opus-4-8")
    form.base.setText("")
    form.key.setText("")
    form.add_to_config(main.csvpath_config)
    form.update_table()

    for r in range(form.table.rowCount()):
        name_item = form.table.item(r, 0)
        if name_item and name_item.text() == "model":
            val_item = form.table.item(r, 1)
            assert val_item is not None
            assert val_item.text() == "claude-opus-4-8", (
                f"Actuals table must show 'claude-opus-4-8' for model; "
                f"got {val_item.text()!r}"
            )
            return
    raise AssertionError("'model' row not found in actuals table")


# ---------------------------------------------------------------------------
# Button smoke tests (no Finder / file-open side effects)
# ---------------------------------------------------------------------------


def test_llm_open_ai_config_calls_open_file(monkeypatch, qtbot, main):
    """
    Clicking 'Open AI config file' must call osut.open_file() with a path
    ending in 'generator.ini'.

    osut.open_file is monkeypatched to prevent actually opening a file.
    """
    form = _form(main)
    opened = []
    monkeypatch.setattr(osut, "open_file", lambda path: opened.append(path))

    form.on_click_ai_idi()

    assert len(opened) == 1, (
        f"osut.open_file must be called once; got {len(opened)} calls"
    )
    assert opened[0].endswith("generator.ini"), (
        f"open_file must receive a generator.ini path; got {opened[0]!r}"
    )


def test_llm_open_metadata_dir_does_not_crash(monkeypatch, qtbot, main, tmp_path):
    """
    Clicking 'Open metadata dir' must not raise an exception.

    on_click_open() calls geut.new_generator_config() → gconfig.configpath /
    gconfig.get("storage","root") → fiut.join_local_overlapped() → Nos.makedirs()
    or os.system() to open the directory in Finder.

    geut.new_generator_config is monkeypatched with a minimal stub so the test
    is isolated from GeneratorConfig.__init__, which does filesystem work (log
    file path resolution, RawConfigParser.read) that can block when logging
    handlers from earlier RunWorker tests hold file locks.  os.system is
    monkeypatched to prevent the actual Finder open from running.
    """
    from flightpath.util import generator_utility as geut_module

    form = _form(main)

    class _StubConfig:
        configpath = str(tmp_path / "generator.ini")

        def get(self, section, name, default=None):
            # Return a relative path so fiut.join_local_overlapped lands inside tmp_path
            return "storage"

    monkeypatch.setattr(geut_module.GeneratorUtility, "new_generator_config",
                        classmethod(lambda cls, main: _StubConfig()))
    monkeypatch.setattr(os, "system", lambda cmd: None)

    try:
        form.on_click_open()
    except Exception as exc:
        raise AssertionError(
            f"on_click_open() must not raise; got {type(exc).__name__}: {exc}"
        ) from exc
