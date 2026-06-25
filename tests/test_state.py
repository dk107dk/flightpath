"""
Unit tests for State (flightpath/util/state.py).

State reads/writes ~/.flightpath and creates directories under ~/FlightPath/.
Isolation strategy:
  - monkeypatch pathlib.Path.home() to return tmp_path, so all directory
    creation and cwd composition happens inside the pytest temp directory.
  - Set state.state_path before any property access to redirect the state
    file itself.

This means every test gets a completely fresh, sandboxed State that never
touches the real user home directory.

Run with:
  poetry run python -m pytest tests/test_state.py -v
"""

import json
import os
import sys
from pathlib import Path

import pytest

from flightpath.util.state import State


# ---------------------------------------------------------------------------
# Fixture
# ---------------------------------------------------------------------------


@pytest.fixture
def isolated_state(tmp_path, monkeypatch):
    """
    A State instance fully isolated inside tmp_path.
    Path.home() returns tmp_path so all directory creation and cwd
    composition happen inside the pytest temp directory.

    state_path is NOT pre-set: the property auto-creates the state file
    on first access, which triggers _create_new_state_file and populates
    the default integrations list.  Pre-setting it would bypass that step
    and leave an empty state file.
    """
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
    state = State()
    return state


# ---------------------------------------------------------------------------
# State file creation
# ---------------------------------------------------------------------------


def test_new_state_file_is_created_on_first_access(isolated_state, tmp_path):
    _ = isolated_state.data
    assert (tmp_path / ".flightpath").exists()


def test_new_state_file_is_valid_json(isolated_state, tmp_path):
    _ = isolated_state.data
    content = (tmp_path / ".flightpath").read_text()
    parsed = json.loads(content)
    assert isinstance(parsed, dict)


def test_new_state_file_contains_integrations_list(isolated_state):
    data = isolated_state.data
    assert "integrations" in data
    assert isinstance(data["integrations"], list)
    assert len(data["integrations"]) > 0


def test_data_setter_none_raises(isolated_state):
    with pytest.raises(ValueError, match="State cannot be None"):
        isolated_state.data = None


# ---------------------------------------------------------------------------
# data read / write roundtrip
# ---------------------------------------------------------------------------


def test_data_roundtrip(isolated_state):
    isolated_state.data = {"key": "value", "count": 42}
    assert isolated_state.data == {"key": "value", "count": 42}


def test_successive_writes_last_wins(isolated_state):
    isolated_state.data = {"key": "first"}
    isolated_state.data = {"key": "second"}
    assert isolated_state.data["key"] == "second"


# ---------------------------------------------------------------------------
# current_project
# ---------------------------------------------------------------------------


def test_current_project_defaults_to_Default(isolated_state):
    assert isolated_state.current_project == State.DEFAULT_PROJECT_NAME


def test_current_project_set_and_get(isolated_state):
    isolated_state.current_project = "MyProject"
    assert isolated_state.current_project == "MyProject"


def test_current_project_strips_os_sep_suffix(isolated_state):
    """A project name stored with a trailing separator is trimmed on read."""
    data = isolated_state.data
    data["current_project"] = f"MyProject{os.sep}subdir"
    isolated_state.data = data
    assert isolated_state.current_project == "MyProject"


def test_current_project_empty_string_falls_back_to_default(isolated_state):
    data = isolated_state.data
    data["current_project"] = "   "
    isolated_state.data = data
    assert isolated_state.current_project == State.DEFAULT_PROJECT_NAME


# ---------------------------------------------------------------------------
# projects_home
# ---------------------------------------------------------------------------


def test_projects_home_defaults_to_FlightPath(isolated_state):
    assert isolated_state.projects_home == State.DEFAULT_PROJECTS_DIR


def test_projects_home_set_and_get(isolated_state):
    isolated_state.projects_home = "MyProjects"
    assert isolated_state.projects_home == "MyProjects"


def test_projects_home_set_none_removes_key(isolated_state):
    isolated_state.projects_home = "MyProjects"
    isolated_state.projects_home = None
    data = isolated_state.data
    assert "projects_home" not in data


# ---------------------------------------------------------------------------
# cwd
# ---------------------------------------------------------------------------


def test_cwd_is_composed_from_home_projects_and_project(isolated_state, tmp_path):
    isolated_state.projects_home = "FP"
    isolated_state.current_project = "Alpha"
    expected = str(tmp_path / "FP" / "Alpha")
    assert isolated_state.cwd == expected


def test_cwd_changes_when_current_project_changes(isolated_state):
    isolated_state.current_project = "ProjectA"
    cwd_a = isolated_state.cwd
    isolated_state.current_project = "ProjectB"
    cwd_b = isolated_state.cwd
    assert cwd_a != cwd_b
    assert cwd_b.endswith("ProjectB")


def test_has_cwd_returns_true(isolated_state):
    assert isolated_state.has_cwd() is True


# ---------------------------------------------------------------------------
# set_env / load_env
# ---------------------------------------------------------------------------


def test_set_env_persists_to_state_file(isolated_state):
    isolated_state.set_env("MY_VAR", "hello")
    data = isolated_state.data
    assert data["env"]["MY_VAR"] == "hello"


def test_load_env_sets_os_environ(isolated_state, monkeypatch):
    isolated_state.set_env("TEST_KEY", "test_value")
    monkeypatch.delenv("TEST_KEY", raising=False)
    isolated_state.load_env()
    assert os.environ.get("TEST_KEY") == "test_value"


def test_set_env_none_value_removes_key(isolated_state):
    isolated_state.set_env("GONE", "present")
    isolated_state.set_env("GONE", None)
    data = isolated_state.data
    assert "GONE" not in data.get("env", {})


def test_load_env_with_no_env_dict_is_no_op(isolated_state):
    """If state has no 'env' key, load_env creates an empty dict and does not raise."""
    data = isolated_state.data
    data.pop("env", None)
    isolated_state.data = data
    isolated_state.load_env()
    assert isolated_state.data.get("env") == {}


# ---------------------------------------------------------------------------
# _change_function_path
# ---------------------------------------------------------------------------


def test_change_function_path_none_new_config_raises(isolated_state):
    with pytest.raises(ValueError, match="New config cannot be None"):
        isolated_state._change_function_path(new_config=None)


def test_change_function_path_adds_dir_to_sys_path(isolated_state, tmp_path):
    """A new config with a functions imports path adds its dirname to sys.path."""
    imports_file = tmp_path / "config" / "functions.imports"
    imports_file.parent.mkdir(parents=True, exist_ok=True)
    imports_file.touch()

    class FakeConfig:
        def get(self, section, name):
            if section == "functions" and name == "imports":
                return str(imports_file)
            return ""

    expected_dir = str(imports_file.parent)
    try:
        isolated_state._change_function_path(new_config=FakeConfig())
        assert expected_dir in sys.path
    finally:
        if expected_dir in sys.path:
            sys.path.remove(expected_dir)


def test_change_function_path_removes_old_dir_from_sys_path(isolated_state, tmp_path):
    """Switching configs removes the old functions dir from sys.path."""
    old_dir = tmp_path / "old_config"
    old_dir.mkdir()
    old_imports = old_dir / "functions.imports"
    old_imports.touch()

    new_dir = tmp_path / "new_config"
    new_dir.mkdir()
    new_imports = new_dir / "functions.imports"
    new_imports.touch()

    class FakeConfig:
        def __init__(self, imports_path):
            self._path = imports_path

        def get(self, section, name):
            if section == "functions" and name == "imports":
                return self._path
            return ""

    old_config = FakeConfig(str(old_imports))
    new_config = FakeConfig(str(new_imports))

    sys.path.append(str(old_dir))
    try:
        isolated_state._change_function_path(
            old_config=old_config, new_config=new_config
        )
        assert str(old_dir) not in sys.path
        assert str(new_dir) in sys.path
    finally:
        for d in [str(old_dir), str(new_dir)]:
            if d in sys.path:
                sys.path.remove(d)
