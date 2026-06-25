"""
Unit tests for ConfigForm.make_path()
(flightpath/widgets/config_forms/config_form.py).

make_path() normalises a user-supplied env-file path into an absolute path
rooted at cwd/config/.  It has two short-circuit returns ("env") for empty or
sentinel inputs, and one ValueError guard for cwd=None when a real path is
given.

Replaces test_env_file.py: the original file tested the same method but packed
all 11 path permutations into a single assertion-per-line function.  Each case
is now its own named test.

Run with:
  poetry run python -m pytest tests/test_config_form.py -v
"""

import os

import pytest

from flightpath.widgets.config_forms.config_form import ConfigForm

# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

SEP = os.sep
CWD = f"{SEP}d{SEP}k{SEP}fp{SEP}cp"
CP  = "cp"


def _make(path, cwd=CWD, current_project=CP):
    return ConfigForm.make_path(path=path, cwd=cwd, current_project=current_project)


# ---------------------------------------------------------------------------
# Short-circuit: returns "env" without touching cwd
# ---------------------------------------------------------------------------


def test_whitespace_only_path_returns_env():
    assert _make(" ") == "env"


def test_none_path_returns_env():
    """None path is falsy and short-circuits before cwd is checked."""
    assert _make(None) == "env"


def test_env_sentinel_returns_env():
    assert _make("env") == "env"


def test_env_sentinel_with_spaces_returns_env():
    assert _make("  env  ") == "env"


# ---------------------------------------------------------------------------
# cwd=None guard
# ---------------------------------------------------------------------------


def test_cwd_none_with_real_path_raises():
    """When path is not empty/env and cwd is None, ValueError is raised."""
    with pytest.raises(ValueError, match="cannot be None"):
        _make("env.json", cwd=None)


def test_cwd_none_with_none_path_still_returns_env():
    """None path short-circuits before the cwd guard — no ValueError."""
    assert _make(None, cwd=None) == "env"


# ---------------------------------------------------------------------------
# current_project=None — falls back to basename(cwd)
# ---------------------------------------------------------------------------


def test_current_project_none_falls_back_to_cwd_basename():
    """When current_project is None, make_path uses os.path.basename(cwd)."""
    result = _make("env.json", current_project=None)
    assert result == f"{CWD}{SEP}config{SEP}env.json"


# ---------------------------------------------------------------------------
# Relative paths (no leading separator)
# ---------------------------------------------------------------------------


def test_config_prefix_relative_path():
    """A relative path starting with config/ is joined directly to cwd."""
    result = _make(f" config{SEP}env.json")
    assert result == f"{CWD}{SEP}config{SEP}env.json"


def test_bare_filename_gets_config_dir_prepended():
    """A bare filename with no directory prefix lands in cwd/config/."""
    result = _make("env.json ")
    assert result == f"{CWD}{SEP}config{SEP}env.json"


def test_subdirectory_path_gets_config_dir_prepended():
    """A relative path with a custom subdir is placed under cwd/config/."""
    result = _make(f"fish{SEP}env.json")
    assert result == f"{CWD}{SEP}config{SEP}fish{SEP}env.json"


# ---------------------------------------------------------------------------
# Absolute paths (leading separator) — only the basename is kept
# ---------------------------------------------------------------------------


def test_absolute_path_with_config_prefix_basename_only():
    """/config/env.json → only 'env.json' is kept, placed under cwd/config/."""
    result = _make(f"{SEP}config{SEP}env.json")
    assert result == f"{CWD}{SEP}config{SEP}env.json"


def test_absolute_path_under_different_dir_basename_only():
    """/fish/env.json → only 'env.json' is kept, placed under cwd/config/."""
    result = _make(f"{SEP}fish{SEP}env.json")
    assert result == f"{CWD}{SEP}config{SEP}env.json"


def test_absolute_path_from_different_project_basename_only():
    """An absolute path rooted in a different project directory is treated
    as an absolute path: only the basename is extracted."""
    other = f"{SEP}d{SEP}k{SEP}fp{SEP}other{SEP}env.json"
    result = _make(other)
    assert result == f"{CWD}{SEP}config{SEP}env.json"


# ---------------------------------------------------------------------------
# Full cwd-rooted paths (contain current_project as a component)
# ---------------------------------------------------------------------------


def test_full_path_with_env_filename_inserts_config():
    """cwd/env.json → config/ is inserted between cwd and the filename."""
    result = _make(f"{CWD}{SEP}env.json")
    assert result == f"{CWD}{SEP}config{SEP}env.json"


def test_full_path_already_correct_returned_unchanged():
    """cwd/config/env.json is already the canonical form; returned as-is."""
    result = _make(f"{CWD}{SEP}config{SEP}env.json")
    assert result == f"{CWD}{SEP}config{SEP}env.json"


def test_full_path_with_wrong_subdir_inserts_config():
    """cwd/fish/env.json → config/ is inserted, preserving the subdir."""
    result = _make(f"{CWD}{SEP}fish{SEP}env.json")
    assert result == f"{CWD}{SEP}config{SEP}fish{SEP}env.json"


# ---------------------------------------------------------------------------
# cwd does not end with current_project
# ---------------------------------------------------------------------------


def test_cwd_not_ending_with_current_project():
    """make_path uses current_project to locate the relative part of path,
    then prepends the actual cwd — so a mismatch just means cwd is used
    as the root regardless."""
    other_cwd = f"{SEP}d{SEP}k{SEP}fp{SEP}other"
    result = _make("env.json", cwd=other_cwd, current_project=CP)
    assert result == f"{other_cwd}{SEP}config{SEP}env.json"
