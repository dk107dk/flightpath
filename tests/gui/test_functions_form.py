"""
pytest-qt tests for FunctionsForm.

Checklist coverage:
  CONFIG > functions section — register a custom function — appears in function list

== FunctionsForm overview ==

FunctionsForm has one editable field:
  imports_dir_path — path to a Python imports file that registers custom functions

  add_to_config() — writes the field value to config["functions"]["imports"]
  populate()      — reads config["functions"]["imports"] into the field
  on_click_reset() — if path is non-empty, calls FunctionFactory.clear_to_reload(path)
                     which re-imports the module and registers the custom functions

The form also inherits a BlankForm actuals table (fields = ["imports"]) that
shows the current resolved value of config["functions"]["imports"].

Note: there is no separate "function list" widget in the GUI — the actuals table
IS the display for the registered imports path.

Run with:
  QT_QPA_PLATFORM=offscreen poetry run python -m pytest tests/gui/test_functions_form.py -v
"""

from csvpath.matching.functions.function_factory import FunctionFactory

# isolated_home and main fixtures provided by conftest.py


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _form(main):
    main.open_config()
    form = main.config.config_panel.get_form("functions")
    assert form is not None, "FunctionsForm must be present in config panel"
    return form


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_functions_form_imports_path_saved_to_config(qtbot, main):
    """
    Setting imports_dir_path and calling add_to_config() must write the value
    to config["functions"]["imports"].

    The value is read back via main.csvpath_config.get() to confirm it was
    persisted in the in-memory config (save_config() is called separately by
    the config panel's save_all_forms()).
    """
    form = _form(main)
    form.imports_dir_path.setText("/tmp/my_functions.py")

    form.add_to_config(main.csvpath_config)

    actual = main.csvpath_config.get(section="functions", name="imports")
    assert actual == "/tmp/my_functions.py", (
        f'config["functions"]["imports"] must be "/tmp/my_functions.py" after '
        f"add_to_config(); got {actual!r}"
    )


def test_functions_form_imports_path_restored_on_populate(qtbot, main):
    """
    Calling populate() must read config["functions"]["imports"] and display it
    in imports_dir_path.

    The test writes a value directly to config then calls populate() to verify
    the form reflects the stored value without a full config-panel rebuild.
    """
    form = _form(main)
    main.csvpath_config.add_to_config("functions", "imports", "/opt/custom_fns.py")

    form.populate()

    assert form.imports_dir_path.text() == "/opt/custom_fns.py", (
        "imports_dir_path must display the config value after populate(); "
        f"got {form.imports_dir_path.text()!r}"
    )


def test_functions_form_actuals_table_shows_imports_field(qtbot, main):
    """
    After update_table(), the actuals table (inherited from BlankForm) must
    show 'imports' in the Name column.

    The actuals table is created because FunctionsForm.fields returns
    ["imports"].  Row 0 must have "imports" in column 0.
    """
    form = _form(main)
    form.imports_dir_path.setText("/tmp/fns.py")
    form.add_to_config(main.csvpath_config)
    form.update_table()

    assert form.table is not None, "FunctionsForm must have an actuals table"
    assert form.table.rowCount() >= 1, "Actuals table must have at least one row"
    name_item = form.table.item(0, 0)
    assert name_item is not None, "Actuals table row 0, col 0 must not be None"
    assert name_item.text() == "imports", (
        f"Actuals table must show 'imports' in name column; got {name_item.text()!r}"
    )


def test_functions_form_actuals_table_shows_imports_value(qtbot, main):
    """
    After add_to_config() and update_table(), the actuals table Value column
    must show the imports path stored in config.
    """
    form = _form(main)
    form.imports_dir_path.setText("/tmp/my_fns.py")
    form.add_to_config(main.csvpath_config)
    form.update_table()

    value_item = form.table.item(0, 1)
    assert value_item is not None, "Actuals table row 0, col 1 must not be None"
    assert value_item.text() == "/tmp/my_fns.py", (
        f"Actuals table Value must show the saved imports path; "
        f"got {value_item.text()!r}"
    )


def test_functions_form_reload_skipped_for_empty_path(monkeypatch, qtbot, main):
    """
    on_click_reset() must return early without calling FunctionFactory when
    imports_dir_path is empty.

    The guard prevents a FunctionFactory.clear_to_reload() call with an empty
    or whitespace-only path that would cause an import error.
    """
    form = _form(main)
    form.imports_dir_path.setText("")

    calls = []
    monkeypatch.setattr(
        FunctionFactory,
        "clear_to_reload",
        staticmethod(lambda path: calls.append(path)),
    )

    form.on_click_reset()

    assert len(calls) == 0, (
        "FunctionFactory.clear_to_reload must NOT be called when path is empty; "
        f"got {calls!r}"
    )


def test_functions_form_reload_calls_factory_with_path(monkeypatch, qtbot, main):
    """
    on_click_reset() must call FunctionFactory.clear_to_reload() with the
    imports_dir_path text when the path is non-empty.

    FunctionFactory.clear_to_reload is monkeypatched to capture the call
    without triggering real module imports.
    """
    form = _form(main)
    form.imports_dir_path.setText("/tmp/my_functions.py")

    calls = []
    monkeypatch.setattr(
        FunctionFactory,
        "clear_to_reload",
        staticmethod(lambda path: calls.append(path)),
    )

    form.on_click_reset()

    assert len(calls) == 1, (
        "FunctionFactory.clear_to_reload must be called once for a non-empty path; "
        f"got {len(calls)} calls"
    )
    assert calls[0] == "/tmp/my_functions.py", (
        f"clear_to_reload must receive the imports_dir_path value; got {calls[0]!r}"
    )
