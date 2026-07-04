"""
Tests for ProjectsForm — the Config Panel > Projects tab.

== ProjectsForm overview ==

ProjectsForm shows the projects-directory setting (stored in ~/.flightpath,
not in config.ini).  The field is editable; a dedicated "Set Directory" button
applies the change after a confirmation prompt.  The Config panel Save and Reset
buttons do not touch this setting.

  populate()          — fills project_dir with state.projects_home; disables Set button
  add_to_config()     — intentional no-op: setting is managed via Set Directory only
  on_set_directory()  — validates, prompts, then updates state and reloads the project
  _on_dir_changed()   — enables/disables Set button based on whether text changed

Run with:
  QT_QPA_PLATFORM=offscreen poetry run python -m pytest tests/gui/test_projects_form.py -v
"""

from csvpath.util.nos import Nos
from PySide6.QtWidgets import QMessageBox

from flightpath.widgets.config_forms.projects_form import ProjectsForm


# isolated_home and main fixtures provided by conftest.py


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _form(main) -> ProjectsForm:
    main.open_config()
    assert main.config.config_panel.ready, "Config panel must be ready after open_config()"
    form = main.config.config_panel.get_form("ProjectsForm")
    assert form is not None, "ProjectsForm must be present in the config panel"
    assert isinstance(form, ProjectsForm)
    return form


# ---------------------------------------------------------------------------
# Populate and display
# ---------------------------------------------------------------------------


def test_projects_form_displays_projects_home(qtbot, main):
    """
    After populate(), project_dir must show the current value of
    main.state.projects_home.
    """
    form = _form(main)
    expected = main.state.projects_home
    assert expected, "state.projects_home must be non-empty after project creation"
    assert form.project_dir.text() == expected, (
        f"project_dir must display state.projects_home {expected!r}; "
        f"got {form.project_dir.text()!r}"
    )


def test_projects_form_populate_refreshes_display(qtbot, main):
    """
    Calling populate() after changing state.projects_home must update the field.
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


# ---------------------------------------------------------------------------
# Field editability
# ---------------------------------------------------------------------------


def test_projects_dir_field_is_editable(qtbot, main):
    """project_dir QLineEdit must not be read-only."""
    form = _form(main)
    assert not form.project_dir.isReadOnly(), "projects dir field must be editable"


# ---------------------------------------------------------------------------
# Config-panel Save button must NOT be affected
# ---------------------------------------------------------------------------


def test_typing_in_projects_dir_does_not_enable_save_button(qtbot, main):
    """
    Typing in the projects-dir field must not enable the config-panel Save
    button.  The setting lives in ~/.flightpath, not config.ini, so it has
    nothing to do with the config panel save/reset toolbar.
    """
    form = _form(main)
    assert not main.config.toolbar._button_save.isEnabled(), (
        "Save button must start disabled"
    )
    form.project_dir.setText("SomeOtherDir")
    assert not main.config.toolbar._button_save.isEnabled(), (
        "Save button must NOT be enabled after editing the projects-dir field"
    )


# ---------------------------------------------------------------------------
# add_to_config is a no-op
# ---------------------------------------------------------------------------


def test_add_to_config_is_noop(qtbot, main):
    """
    add_to_config() must not change state.projects_home.  The setting is now
    managed exclusively via the Set Directory button; the config panel Save
    button must not touch it.
    """
    form = _form(main)
    original = main.state.projects_home
    form.add_to_config(main.csvpath_config)
    assert main.state.projects_home == original, (
        "add_to_config() must not change state.projects_home"
    )


# ---------------------------------------------------------------------------
# Set Directory button state
# ---------------------------------------------------------------------------


def test_set_button_starts_disabled(qtbot, main):
    """Set Directory button must be disabled when the field matches projects_home."""
    form = _form(main)
    assert not form.set_button.isEnabled(), (
        "Set Directory button must be disabled when text equals current projects_home"
    )


def test_set_button_enabled_when_text_changes(qtbot, main):
    """Set Directory button enables when the field text differs from projects_home."""
    form = _form(main)
    form.project_dir.setText("NewProjectsDir")
    assert form.set_button.isEnabled(), (
        "Set Directory button must be enabled when text differs from current projects_home"
    )


def test_set_button_disabled_when_text_restored(qtbot, main):
    """Set Directory button re-disables when the text is reset to the original value."""
    form = _form(main)
    original = main.state.projects_home
    form.project_dir.setText("NewProjectsDir")
    assert form.set_button.isEnabled()
    form.project_dir.setText(original)
    assert not form.set_button.isEnabled(), (
        "Set Directory button must disable when text is restored to current projects_home"
    )


# ---------------------------------------------------------------------------
# Set Directory blocked by unsaved config changes
# ---------------------------------------------------------------------------


def test_set_directory_blocked_by_unsaved_config_changes(qtbot, main, monkeypatch):
    """
    If there are unsaved config changes, Set Directory must show a blocking
    message and must not proceed with the directory change.
    """
    form = _form(main)
    form.project_dir.setText("NewProjectsDir")

    captured = []
    monkeypatch.setattr(
        "flightpath.widgets.config_forms.projects_form.meut.message2",
        lambda **kwargs: captured.append(kwargs),
    )
    monkeypatch.setattr(main, "_has_config_changes", lambda: True)

    form.on_set_directory()

    assert len(captured) == 1, "A blocking message2 must be shown"
    assert "Unsaved" in captured[0]["title"]
    assert main.state.projects_home != "NewProjectsDir", (
        "state.projects_home must not change when blocked by unsaved config changes"
    )


# ---------------------------------------------------------------------------
# Confirmation prompt
# ---------------------------------------------------------------------------


def test_set_directory_shows_confirmation_prompt(qtbot, main, monkeypatch):
    """
    Clicking Set Directory (no unsaved config changes) must open a yesNo2
    confirmation dialog that names the target directory.
    """
    form = _form(main)
    form.project_dir.setText("NewProjectsDir")

    monkeypatch.setattr(main, "_has_config_changes", lambda: False)
    captured = []
    monkeypatch.setattr(
        "flightpath.widgets.config_forms.projects_form.meut.yesNo2",
        lambda **kwargs: captured.append(kwargs),
    )

    form.on_set_directory()

    assert len(captured) == 1, "yesNo2 must be called once"
    assert "NewProjectsDir" in captured[0]["msg"], (
        "Confirmation message must name the target directory"
    )


# ---------------------------------------------------------------------------
# Confirm: state updated and reload triggered
# ---------------------------------------------------------------------------


def test_set_directory_confirm_updates_state(qtbot, main, monkeypatch):
    """
    Confirming the prompt must update state.projects_home, reset current_project
    to Default, and call load_state_and_cd().
    """
    form = _form(main)
    new_home = "TestProjectsDir_Confirm"

    monkeypatch.setattr(main, "_has_config_changes", lambda: False)
    monkeypatch.setattr(Nos, "exists", lambda self: True)
    monkeypatch.setattr(main, "is_writable", lambda path: True)

    reload_called = []
    monkeypatch.setattr(main, "load_state_and_cd", lambda: reload_called.append(True))
    monkeypatch.setattr(main, "cancel_config_changes", lambda: None)

    form._on_confirm_set_directory(QMessageBox.Yes, new_home=new_home)

    assert main.state.projects_home == new_home, (
        "state.projects_home must be updated after confirmation"
    )
    assert main.state.current_project == main.state.DEFAULT_PROJECT_NAME, (
        "current_project must be reset to Default after changing the projects directory"
    )
    assert len(reload_called) == 1, "load_state_and_cd() must be called after confirmation"


# ---------------------------------------------------------------------------
# Cancel: state unchanged
# ---------------------------------------------------------------------------


def test_set_directory_cancel_does_not_update_state(qtbot, main, monkeypatch):
    """
    Cancelling the confirmation must leave state.projects_home unchanged and
    restore the field text to the original value.
    """
    form = _form(main)
    original_home = main.state.projects_home

    monkeypatch.setattr(main, "_has_config_changes", lambda: False)

    form._on_confirm_set_directory(QMessageBox.No, new_home="ShouldNotBeSet")

    assert main.state.projects_home == original_home, (
        "state.projects_home must be unchanged after cancelling"
    )
    assert form.project_dir.text() == original_home, (
        "field text must be restored to original projects_home after cancel"
    )
    assert not form.set_button.isEnabled(), (
        "Set button must be disabled after cancel restores the original text"
    )
