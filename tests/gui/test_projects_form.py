"""
pytest-qt tests for ProjectsForm.

Checklist coverage:
  CONFIG > project form — project-level metadata saved

== ProjectsForm overview ==

ProjectsForm has a single read-only QLineEdit (project_dir) that displays
main.state.projects_home — the relative directory name under state.home where
all FlightPath projects live (e.g. "FlightPath").

  populate()        — sets project_dir.setText(state.projects_home)
  add_to_config()   — reads project_dir.text(), ensures the directory exists,
                      then sets state.projects_home if the path is writable

Because project_dir is read-only the field cannot be edited through the GUI;
add_to_config() is effectively an idempotent persistence call that confirms the
currently displayed path is still valid and writable.

Run with:
  QT_QPA_PLATFORM=offscreen poetry run python -m pytest tests/gui/test_projects_form.py -v
"""

# isolated_home and main fixtures provided by conftest.py


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _form(main):
    main.open_config()
    form = main.config.config_panel.get_form("ProjectsForm")
    assert form is not None, "ProjectsForm must be present in config panel"
    return form


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_projects_form_displays_projects_home(qtbot, main):
    """
    After populate(), the read-only project_dir field must show the current
    value of main.state.projects_home.

    The isolated_home fixture redirects State.home to a tmp directory.  The
    default projects_home ("FlightPath") is set by State on first run.
    populate() is called automatically during setup_forms().
    """
    form = _form(main)

    expected = main.state.projects_home
    assert expected, "state.projects_home must be non-empty after project creation"
    assert form.project_dir.text() == expected, (
        f"project_dir must display state.projects_home {expected!r}; "
        f"got {form.project_dir.text()!r}"
    )


def test_projects_form_field_is_read_only(qtbot, main):
    """
    The project_dir QLineEdit must be read-only.

    The projects home path is managed by FlightPath state, not typed by the
    user.  Verifying isReadOnly() guards against accidental removal of that
    constraint in a future refactor.
    """
    form = _form(main)
    assert form.project_dir.isReadOnly(), "project_dir must be read-only"


def test_projects_form_add_to_config_preserves_projects_home(qtbot, main):
    """
    Calling add_to_config() must leave state.projects_home unchanged when the
    path already exists and is writable.

    In the isolated test environment the projects home directory is created
    during MainWindow startup, so add_to_config() should find it writable and
    simply re-affirm the existing value.
    """
    form = _form(main)
    original = main.state.projects_home

    form.add_to_config(main.csvpath_config)

    assert main.state.projects_home == original, (
        f"state.projects_home must remain {original!r} after add_to_config(); "
        f"got {main.state.projects_home!r}"
    )


def test_projects_form_populate_refreshes_display(qtbot, main):
    """
    Calling populate() after programmatically changing state.projects_home must
    update the displayed field to the new value.

    This exercises the populate→display link independent of the startup cycle.
    """
    form = _form(main)
    original = main.state.projects_home

    try:
        main.state.projects_home = "AltProjects"
        form.populate()
        assert form.project_dir.text() == "AltProjects", (
            "project_dir must reflect the updated projects_home after populate()"
        )
    finally:
        main.state.projects_home = original
