"""
Tests for the Stage Non-Local File feature.

== Architecture overview ==

StageNonLocalDialog — non-local staging dialog opened from the sidebar
    empty-space right-click menu.
DownloadWorker     — QRunnable that copies a remote URI to a local project
    path using DataFileReader / DataFileWriter (smart-open backed).

Section 1: DownloadWorker unit tests
    Monkeypatch DataFileReader and DataFileWriter; check signal payloads
    without touching any real filesystem or network.

Section 2: StageNonLocalDialog unit tests (lightweight mock parents)
    Instantiate the dialog with stub main/sidebar objects to exercise
    validation logic, SFTP config lookup, URI plausibility, and UI state —
    without needing a real MainWindow.

Section 3: Context-menu integration tests (real main fixture)
    Verify that the empty-space menu contains "Stage non-local file" and
    that the dialog is wired correctly.

Run with:
    QT_QPA_PLATFORM=offscreen poetry run python -m pytest \
        tests/gui/test_stage_nonlocal_dialog.py -v
"""

import os
from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtCore import QThreadPool
from PySide6.QtWidgets import QWidget

from flightpath.workers.download_worker import DownloadWorker
from flightpath.dialogs.stage_nonlocal_dialog import StageNonLocalDialog


# ---------------------------------------------------------------------------
# Section 1 — DownloadWorker unit tests
# ---------------------------------------------------------------------------


def _make_download_worker(uri="sftp://host/file.csv", local_path="/tmp/file.csv"):
    return DownloadWorker(uri=uri, local_path=local_path)


def test_download_worker_raises_on_empty_uri():
    with pytest.raises(ValueError, match="uri"):
        DownloadWorker(uri="", local_path="/tmp/file.csv")


def test_download_worker_raises_on_empty_local_path():
    with pytest.raises(ValueError, match="local_path"):
        DownloadWorker(uri="sftp://host/file.csv", local_path="")


def test_download_worker_emits_true_on_success(qtbot, tmp_path, monkeypatch):
    dest = str(tmp_path / "out.csv")

    class _FakeReader:
        def __init__(self, *a, **kw):
            pass
        def __enter__(self):
            return self
        def __exit__(self, *a):
            pass
        def read(self):
            return "col1,col2\n1,2\n"

    class _FakeWriter:
        def __init__(self, *a, **kw):
            pass
        def __enter__(self):
            return self
        def __exit__(self, *a):
            pass
        def write(self, data):
            pass

    monkeypatch.setattr(
        "flightpath.workers.download_worker.DataFileReader", _FakeReader
    )
    monkeypatch.setattr(
        "flightpath.workers.download_worker.DataFileWriter", _FakeWriter
    )
    monkeypatch.setattr("os.makedirs", lambda *a, **kw: None)

    captured = []
    worker = DownloadWorker(uri="sftp://host/file.csv", local_path=dest)
    worker.signals.finished.connect(lambda ok, p: captured.append((ok, p)))
    worker.run()

    assert len(captured) == 1
    assert captured[0][0] is True
    assert captured[0][1] == dest


def test_download_worker_emits_false_on_reader_error(qtbot, tmp_path, monkeypatch):
    class _BrokenReader:
        def __init__(self, *a, **kw):
            pass
        def __enter__(self):
            raise OSError("connection refused")
        def __exit__(self, *a):
            pass

    monkeypatch.setattr(
        "flightpath.workers.download_worker.DataFileReader", _BrokenReader
    )
    monkeypatch.setattr("os.makedirs", lambda *a, **kw: None)

    captured = []
    worker = DownloadWorker(
        uri="sftp://host/file.csv", local_path=str(tmp_path / "out.csv")
    )
    worker.signals.finished.connect(lambda ok, p: captured.append((ok, p)))
    worker.run()

    assert len(captured) == 1
    assert captured[0][0] is False
    assert "connection refused" in captured[0][1]


# ---------------------------------------------------------------------------
# Section 2 — StageNonLocalDialog unit tests (mock parents)
# ---------------------------------------------------------------------------


def _make_dialog(qtbot, tmp_path):
    """Instantiate and show StageNonLocalDialog with a lightweight stub main.

    The dialog must be shown so that child-widget isVisible() reflects the
    explicit setVisible() calls made by _on_uri_changed and similar handlers.
    Without .show(), Qt's effective-visibility calculation always returns False
    for children of an un-shown top-level window.
    """
    fake_state = MagicMock()
    fake_state.cwd = str(tmp_path)

    fake_config = MagicMock()
    fake_config.get.return_value = ""

    fake_main = MagicMock()
    fake_main.state = fake_state
    fake_main.csvpath_config = fake_config

    fake_sidebar = MagicMock()

    dialog = StageNonLocalDialog(main=fake_main, parent=fake_sidebar)
    qtbot.addWidget(dialog)
    dialog.show()
    qtbot.waitExposed(dialog)
    return dialog, fake_main, fake_sidebar


# --- SFTP config lookup ---


def test_check_sftp_config_returns_false_when_unconfigured(qtbot, tmp_path):
    dialog, fake_main, _ = _make_dialog(qtbot, tmp_path)
    fake_main.csvpath_config.get.return_value = ""

    any_sftp, creds = dialog._check_sftp_config("myhost.example.com")

    assert any_sftp is False
    assert creds is None


def test_check_sftp_config_returns_creds_when_server_matches(qtbot, tmp_path):
    dialog, fake_main, _ = _make_dialog(qtbot, tmp_path)

    def _cfg_get(*, section, name, **kw):
        return {
            ("sftp", "server"): "myhost.example.com",
            ("sftp", "port"): "22",
            ("sftp", "username"): "alice",
            ("sftp", "password"): "secret",
        }.get((section, name), "")

    fake_main.csvpath_config.get.side_effect = _cfg_get

    any_sftp, creds = dialog._check_sftp_config("myhost.example.com")

    assert any_sftp is True
    assert creds is not None
    assert creds["server"] == "myhost.example.com"
    assert creds["username"] == "alice"
    assert creds["port"] == 22


def test_check_sftp_config_returns_none_creds_when_host_mismatched(qtbot, tmp_path):
    dialog, fake_main, _ = _make_dialog(qtbot, tmp_path)

    def _cfg_get(*, section, name, **kw):
        return {
            ("sftp", "server"): "otherhost.example.com",
            ("sftp", "port"): "22",
            ("sftp", "username"): "alice",
            ("sftp", "password"): "secret",
            ("inputs", "files"): "/local/path",
        }.get((section, name), "")

    fake_main.csvpath_config.get.side_effect = _cfg_get

    any_sftp, creds = dialog._check_sftp_config("myhost.example.com")

    assert any_sftp is True
    assert creds is None


def test_check_sftp_config_matches_via_inputs_files(qtbot, tmp_path):
    dialog, fake_main, _ = _make_dialog(qtbot, tmp_path)

    def _cfg_get(*, section, name, **kw):
        return {
            ("sftp", "server"): "mainhost.example.com",
            ("sftp", "port"): "22",
            ("sftp", "username"): "bob",
            ("sftp", "password"): "pass",
            ("inputs", "files"): "sftp://mainhost.example.com/named_files",
        }.get((section, name), "")

    fake_main.csvpath_config.get.side_effect = _cfg_get

    any_sftp, creds = dialog._check_sftp_config("mainhost.example.com")

    assert any_sftp is True
    assert creds is not None


# --- URI / host parsing ---


def test_parse_sftp_host_port_extracts_host_and_explicit_port(qtbot, tmp_path):
    dialog, _, _ = _make_dialog(qtbot, tmp_path)
    host, port = dialog._parse_sftp_host_port("sftp://cloudsftp:2022/myfiles/bug.txt")
    assert host == "cloudsftp"
    assert port == 2022


def test_parse_sftp_host_port_defaults_to_22_when_no_port(qtbot, tmp_path):
    dialog, _, _ = _make_dialog(qtbot, tmp_path)
    host, port = dialog._parse_sftp_host_port("sftp://myhost/some/path/file.csv")
    assert host == "myhost"
    assert port == 22


# --- URI plausibility ---


def test_is_plausible_uri_accepts_valid_remote_paths(qtbot, tmp_path):
    dialog, _, _ = _make_dialog(qtbot, tmp_path)
    assert dialog._is_plausible_uri("s3://bucket/file.csv")
    assert dialog._is_plausible_uri("sftp://host/path/file.csv")
    assert dialog._is_plausible_uri("azure://container/deep/path/file.json")
    assert dialog._is_plausible_uri("gs://bucket/subdir/data.csv")


def test_is_plausible_uri_rejects_incomplete_remote_paths(qtbot, tmp_path):
    dialog, _, _ = _make_dialog(qtbot, tmp_path)
    assert not dialog._is_plausible_uri("s3://bucket")
    assert not dialog._is_plausible_uri("s3://")
    assert not dialog._is_plausible_uri("just/a/local/path")
    assert not dialog._is_plausible_uri("s3://bucket/")


# --- URI change handler / UI state ---


def test_uri_change_remote_shows_copy_row(qtbot, tmp_path):
    dialog, _, _ = _make_dialog(qtbot, tmp_path)
    dialog.uri_ctl.setText("s3://my-bucket/data.csv")

    assert dialog.copy_row.isVisible()
    assert dialog.copy_label.isVisible()


def test_uri_change_remote_checks_copy_by_default(qtbot, tmp_path):
    dialog, _, _ = _make_dialog(qtbot, tmp_path)
    dialog.uri_ctl.setText("s3://my-bucket/data.csv")

    assert dialog.copy_ctl.isChecked()


def test_uri_change_invalid_protocol_disables_stage(qtbot, tmp_path):
    dialog, _, _ = _make_dialog(qtbot, tmp_path)
    dialog.named_file_name_ctl.setText("myfile")
    dialog.uri_ctl.setText("ftp://host/file.csv")

    assert not dialog.stage_button.isEnabled()
    assert dialog.note_label.isVisible()
    assert "Unsupported" in dialog.note_label.text()


def test_uri_change_in_project_local_file_no_copy_row(qtbot, tmp_path):
    f = tmp_path / "data.csv"
    f.write_text("a,b\n1,2\n")

    dialog, _, _ = _make_dialog(qtbot, tmp_path)
    dialog.uri_ctl.setText(str(f))

    assert not dialog.copy_row.isVisible()
    assert dialog.note_label.isVisible()
    assert "in your project" in dialog.note_label.text()


def test_uri_change_nonexistent_file_shows_not_found(qtbot, tmp_path):
    dialog, _, _ = _make_dialog(qtbot, tmp_path)
    dialog.uri_ctl.setText("/does/not/exist.csv")

    assert dialog.note_label.isVisible()
    assert "not found" in dialog.note_label.text().lower()


def test_uri_change_outside_project_shows_copy_row_checked(qtbot, tmp_path):
    outside = tmp_path.parent / "outside.csv"
    outside.write_text("x,y\n1,2\n")

    dialog, _, _ = _make_dialog(qtbot, tmp_path)
    dialog.uri_ctl.setText(str(outside))

    assert dialog.copy_row.isVisible()
    assert dialog.copy_label.isVisible()
    assert dialog.copy_ctl.isChecked()


# --- Dest field auto-checks the checkbox ---


def test_dest_entry_auto_checks_copy_checkbox(qtbot, tmp_path):
    """Typing in the dest field while copy is unchecked must auto-check it."""
    dialog, _, _ = _make_dialog(qtbot, tmp_path)
    dialog.uri_ctl.setText("s3://bucket/data.csv")
    dialog.copy_ctl.setChecked(False)  # manually uncheck the default
    assert not dialog.copy_ctl.isChecked()

    dialog.dest_ctl.setText("inputs/external/")

    assert dialog.copy_ctl.isChecked()


# --- Stage button state ---


def test_stage_disabled_without_name(qtbot, tmp_path):
    dialog, _, _ = _make_dialog(qtbot, tmp_path)
    dialog.uri_ctl.setText("s3://bucket/file.csv")
    # name field is empty
    assert not dialog.stage_button.isEnabled()


def test_stage_disabled_with_implausible_remote_uri(qtbot, tmp_path):
    """Stage must be disabled when the URI has only a bucket and no path."""
    dialog, _, _ = _make_dialog(qtbot, tmp_path)
    dialog.named_file_name_ctl.setText("my_data")
    dialog.uri_ctl.setText("s3://bucket")
    dialog.copy_ctl.setChecked(False)

    assert not dialog.stage_button.isEnabled()


def test_stage_enabled_with_remote_uri_name_and_dest(qtbot, tmp_path):
    """Stage enabled when URI is plausible, name is set, and dest is filled."""
    dialog, _, _ = _make_dialog(qtbot, tmp_path)
    dialog.named_file_name_ctl.setText("my_data")
    dialog.uri_ctl.setText("s3://bucket/file.csv")
    dialog.dest_ctl.setText("inputs/external/")

    assert dialog.stage_button.isEnabled()


def test_stage_enabled_with_remote_uri_name_copy_unchecked(qtbot, tmp_path):
    """Stage enabled when URI is plausible, name is set, and copy is unchecked."""
    dialog, _, _ = _make_dialog(qtbot, tmp_path)
    dialog.named_file_name_ctl.setText("my_data")
    dialog.uri_ctl.setText("s3://bucket/file.csv")
    dialog.copy_ctl.setChecked(False)

    assert dialog.stage_button.isEnabled()


def test_stage_disabled_when_copy_checked_but_dest_empty(qtbot, tmp_path):
    dialog, _, _ = _make_dialog(qtbot, tmp_path)
    dialog.named_file_name_ctl.setText("my_data")
    dialog.uri_ctl.setText("s3://bucket/file.csv")
    dialog.copy_ctl.setChecked(True)
    dialog.dest_ctl.setText("")

    assert not dialog.stage_button.isEnabled()


def test_stage_enabled_when_copy_checked_and_dest_filled(qtbot, tmp_path):
    dialog, _, _ = _make_dialog(qtbot, tmp_path)
    dialog.named_file_name_ctl.setText("my_data")
    dialog.uri_ctl.setText("s3://bucket/file.csv")
    dialog.copy_ctl.setChecked(True)
    dialog.dest_ctl.setText("inputs/external/")

    assert dialog.stage_button.isEnabled()


# --- Confirmation dialog when copy is unchecked on submit ---


def test_stage_click_with_unchecked_copy_shows_yesno_confirmation(
    qtbot, tmp_path, monkeypatch
):
    """Clicking Stage with copy_row visible but copy unchecked must show yesNo2."""
    dialog, _, _ = _make_dialog(qtbot, tmp_path)
    dialog.named_file_name_ctl.setText("my_data")
    dialog.uri_ctl.setText("s3://bucket/data.csv")
    dialog.copy_ctl.setChecked(False)

    captured = []
    monkeypatch.setattr(
        "flightpath.dialogs.stage_nonlocal_dialog.meut.yesNo2",
        lambda **kwargs: captured.append(kwargs),
    )

    dialog._on_stage_clicked()

    assert len(captured) == 1, "yesNo2 must be called once"
    assert "without" in captured[0]["msg"].lower(), (
        "Confirmation must ask about registering without copying"
    )


# --- local_path resolution ---


def test_resolve_local_path_appends_source_name_when_dest_is_dir(qtbot, tmp_path):
    """dest with no extension → treat as directory, append source filename."""
    dialog, _, _ = _make_dialog(qtbot, tmp_path)
    local = dialog._resolve_local_path("sftp://host/some/path/data.csv", "inputs/ext")
    assert local.startswith(str(tmp_path))
    assert local.endswith("data.csv")
    assert "inputs" in local
    assert "ext" in local


def test_resolve_local_path_uses_dest_path_when_same_extension(qtbot, tmp_path):
    """dest = 'bug.txt' (same extension as source) → <cwd>/bug.txt, no double nesting."""
    dialog, _, _ = _make_dialog(qtbot, tmp_path)
    local = dialog._resolve_local_path("/Users/davidkershaw/bug.txt", "bug.txt")
    assert local == str(tmp_path / "bug.txt")


def test_resolve_local_path_uses_dest_path_with_subdir(qtbot, tmp_path):
    """dest = 'copied/bug.txt' → <cwd>/copied/bug.txt, no source filename appended."""
    dialog, _, _ = _make_dialog(qtbot, tmp_path)
    local = dialog._resolve_local_path("/Users/davidkershaw/bug.txt", "copied/bug.txt")
    assert local == str(tmp_path / "copied" / "bug.txt")


def test_resolve_local_path_renames_file_when_extension_differs(qtbot, tmp_path):
    """dest = 'copied/bug.csv' → <cwd>/copied/bug.csv even though source is .txt."""
    dialog, _, _ = _make_dialog(qtbot, tmp_path)
    local = dialog._resolve_local_path("/Users/davidkershaw/bug.txt", "copied/bug.csv")
    assert local == str(tmp_path / "copied" / "bug.csv")


# --- SFTP no-server notice ---


def test_proceed_shows_error_when_resolved_path_is_a_directory(qtbot, tmp_path):
    """If a directory exists at the resolved copy-destination path, _proceed must
    show a clear error instead of passing the directory path to DataFileWriter."""
    # Reproduce the scenario: old behavior created 'bug.csv' as a directory
    (tmp_path / "bug.csv").mkdir()

    dialog, fake_main, _ = _make_dialog(qtbot, tmp_path)
    dialog._uri_is_remote = False

    dialog._proceed(
        uri="/Users/davidkershaw/bug.txt",
        name="test4",
        dest="bug.csv",
        must_copy=True,
    )

    assert dialog.error_label.isVisible()
    assert "directory" in dialog.error_label.text().lower()


def test_sftp_notice_shown_when_no_sftp_configured(qtbot, tmp_path):
    """_start_sftp_check shows the SFTP notice (not red error) when no SFTP server
    is configured at all."""
    dialog, _, _ = _make_dialog(qtbot, tmp_path)
    # Default fake_config returns "" for all gets → no SFTP configured
    dialog._start_sftp_check("sftp://host/data.csv", "my_data", "", False)

    assert dialog.sftp_notice.isVisible()
    assert not dialog.error_label.isVisible()


def test_sftp_notice_label_and_button_include_host_and_name(qtbot, tmp_path):
    """_start_sftp_check must put the hostname and named-file name into the notice
    label and the 'Add' button text."""
    dialog, _, _ = _make_dialog(qtbot, tmp_path)
    dialog._start_sftp_check(
        "sftp://cloudsftp:2022/myfiles/bug.txt", "test7", "", False
    )

    assert "cloudsftp" in dialog.sftp_notice_label.text()
    assert dialog.sftp_add_button.text() == "Add cloudsftp to test7"


def test_sftp_notice_cleared_on_uri_change(qtbot, tmp_path):
    """Editing the URI field must hide the SFTP notice."""
    dialog, _, _ = _make_dialog(qtbot, tmp_path)
    dialog.sftp_notice.setVisible(True)

    dialog.uri_ctl.setText("sftp://host/data.csv")

    assert not dialog.sftp_notice.isVisible()


def test_sftp_add_button_disabled_without_name(qtbot, tmp_path):
    """The 'Add SFTP Named File' button must be disabled when no name is entered."""
    dialog, _, _ = _make_dialog(qtbot, tmp_path)
    dialog.named_file_name_ctl.setText("")

    assert not dialog.sftp_add_button.isEnabled()


def test_sftp_add_button_enabled_with_name(qtbot, tmp_path):
    """The 'Add SFTP Named File' button must be enabled as soon as a name is typed."""
    dialog, _, _ = _make_dialog(qtbot, tmp_path)
    dialog.named_file_name_ctl.setText("my_data")

    assert dialog.sftp_add_button.isEnabled()


def test_configure_sftp_button_opens_integrations_form(qtbot, tmp_path):
    """'Configure SFTP' must open the config panel and switch to the Integrations
    form (forms_layout index 8)."""
    dialog, fake_main, _ = _make_dialog(qtbot, tmp_path)

    dialog._on_configure_sftp_clicked()

    fake_main.open_config.assert_called_once()
    fake_main.config.config_panel.forms_layout.setCurrentIndex.assert_called_with(8)


def _make_mock_configs(host: str, port: int) -> dict:
    """Return a configs dict with one ServerConfig that matches host:port."""
    sc = MagicMock()
    sc.address = host
    sc.port = port
    return {"srv1": sc}


def test_sftp_add_creates_named_file_home_when_not_found(
    qtbot, tmp_path, monkeypatch
):
    """When the named-file doesn't exist, assure_named_file_home() and
    registrar.manifest_path() must be called (inlining assure_named_file()
    from CsvPath Framework 0.0.618)."""
    dialog, fake_main, _ = _make_dialog(qtbot, tmp_path)
    dialog.named_file_name_ctl.setText("my_data")
    dialog.uri_ctl.setText("sftp://host/data.csv")

    fake_main.csvpaths.file_manager.has_named_file.return_value = False
    fake_cfg = MagicMock()
    fake_cfg.sources = {}
    fake_main.csvpaths.file_manager.describer.get_config.return_value = fake_cfg

    mock_sftp_dialog = MagicMock()
    monkeypatch.setattr(
        "flightpath.dialogs.stage_nonlocal_dialog.SftpServersDialog",
        lambda **kwargs: mock_sftp_dialog,
    )

    dialog._on_add_sftp_named_file_clicked()

    fake_main.csvpaths.file_manager.assure_named_file_home.assert_called_once_with("my_data")
    home = fake_main.csvpaths.file_manager.assure_named_file_home.return_value
    fake_main.csvpaths.file_manager.registrar.manifest_path.assert_called_once_with(home)
    # original add_named_file must NOT be called
    fake_main.csvpaths.file_manager.add_named_file.assert_not_called()
    mock_sftp_dialog.show_dialog.assert_called_once()


def test_sftp_add_skips_registration_when_named_file_exists(
    qtbot, tmp_path, monkeypatch
):
    """When the named-file already exists, add_named_file must NOT be called again."""
    dialog, fake_main, _ = _make_dialog(qtbot, tmp_path)
    dialog.named_file_name_ctl.setText("my_data")
    dialog.uri_ctl.setText("sftp://host/data.csv")

    fake_main.csvpaths.file_manager.has_named_file.return_value = True
    fake_cfg = MagicMock()
    fake_cfg.sources = {}
    fake_main.csvpaths.file_manager.describer.get_config.return_value = fake_cfg

    mock_sftp_dialog = MagicMock()
    monkeypatch.setattr(
        "flightpath.dialogs.stage_nonlocal_dialog.SftpServersDialog",
        lambda **kwargs: mock_sftp_dialog,
    )

    dialog._on_add_sftp_named_file_clicked()

    fake_main.csvpaths.file_manager.add_named_file.assert_not_called()
    mock_sftp_dialog.show_dialog.assert_called_once()


def test_sftp_add_proceeds_without_dialog_when_server_already_in_named_file_config(
    qtbot, tmp_path, monkeypatch
):
    """When the URI host:port matches an existing ServerConfig on the named-file,
    _proceed must be called with the pending args and SftpServersDialog must NOT
    be opened."""
    dialog, fake_main, _ = _make_dialog(qtbot, tmp_path)
    dialog.named_file_name_ctl.setText("test7")
    dialog.uri_ctl.setText("sftp://cloudsftp:2022/myfiles/bug.txt")

    # Pre-load a pending stage (normally set by _start_sftp_check)
    dialog._pending_stage = ("sftp://cloudsftp:2022/myfiles/bug.txt", "test7", "", False)

    fake_main.csvpaths.file_manager.has_named_file.return_value = True
    fake_cfg = MagicMock()
    fake_cfg.sources = _make_mock_configs("cloudsftp", 2022)
    fake_main.csvpaths.file_manager.describer.get_config.return_value = fake_cfg

    proceed_calls = []
    monkeypatch.setattr(dialog, "_proceed", lambda *a: proceed_calls.append(a))

    mock_sftp_cls = MagicMock()
    monkeypatch.setattr(
        "flightpath.dialogs.stage_nonlocal_dialog.SftpServersDialog", mock_sftp_cls
    )

    dialog._on_add_sftp_named_file_clicked()

    assert proceed_calls == [
        ("sftp://cloudsftp:2022/myfiles/bug.txt", "test7", "", False)
    ]
    assert dialog._pending_stage is None
    mock_sftp_cls.assert_not_called()


def test_sftp_add_clears_notice_before_opening_dialog(qtbot, tmp_path, monkeypatch):
    """The SFTP notice must be hidden before SftpServersDialog is opened so
    it doesn't linger while the child dialog is on screen."""
    dialog, fake_main, _ = _make_dialog(qtbot, tmp_path)
    dialog.named_file_name_ctl.setText("my_data")
    dialog.uri_ctl.setText("sftp://host/data.csv")
    dialog.sftp_notice.setVisible(True)  # simulate notice showing

    fake_main.csvpaths.file_manager.has_named_file.return_value = True
    fake_cfg = MagicMock()
    fake_cfg.sources = {}
    fake_main.csvpaths.file_manager.describer.get_config.return_value = fake_cfg

    notice_was_hidden = []

    real_show = MagicMock()

    def _capturing_show_dialog():
        notice_was_hidden.append(not dialog.sftp_notice.isVisible())

    mock_sftp = MagicMock()
    mock_sftp.show_dialog.side_effect = _capturing_show_dialog
    monkeypatch.setattr(
        "flightpath.dialogs.stage_nonlocal_dialog.SftpServersDialog",
        lambda **kwargs: mock_sftp,
    )

    dialog._on_add_sftp_named_file_clicked()

    assert notice_was_hidden == [True], "Notice must be hidden before show_dialog() is called"


def test_sftp_add_noops_when_name_is_empty(qtbot, tmp_path, monkeypatch):
    """Calling _on_add_sftp_named_file_clicked with no name must do nothing."""
    dialog, fake_main, _ = _make_dialog(qtbot, tmp_path)
    dialog.named_file_name_ctl.setText("")
    dialog.uri_ctl.setText("sftp://host/data.csv")

    monkeypatch.setattr(
        "flightpath.dialogs.stage_nonlocal_dialog.SftpServersDialog",
        MagicMock(),
    )

    dialog._on_add_sftp_named_file_clicked()

    fake_main.csvpaths.file_manager.add_named_file.assert_not_called()
    fake_main.csvpaths.file_manager.has_named_file.assert_not_called()


def test_set_sftps_saves_config_to_file_manager(qtbot, tmp_path):
    """set_sftps() must write the configs back through describer.store_config()."""
    dialog, fake_main, _ = _make_dialog(qtbot, tmp_path)
    configs = {"srv1": MagicMock()}

    dialog.set_sftps("my_data", configs)

    fake_main.csvpaths.file_manager.describer.get_config.assert_called_with("my_data")
    saved_config = fake_main.csvpaths.file_manager.describer.get_config.return_value
    assert saved_config.sources == configs
    fake_main.csvpaths.file_manager.describer.store_config.assert_called_once()
    assert dialog._pending_stage is None  # no pending → no auto-proceed


def test_set_sftps_auto_proceeds_with_pending_stage(qtbot, tmp_path, monkeypatch):
    """After saving SFTP config, set_sftps must call _proceed with the stored
    pending args so the user doesn't have to click Stage again."""
    dialog, fake_main, _ = _make_dialog(qtbot, tmp_path)
    dialog._pending_stage = ("sftp://host/data.csv", "my_data", "", False)

    proceed_calls = []
    monkeypatch.setattr(dialog, "_proceed", lambda *a: proceed_calls.append(a))

    dialog.set_sftps("my_data", {"srv1": MagicMock()})

    assert proceed_calls == [("sftp://host/data.csv", "my_data", "", False)]
    assert dialog._pending_stage is None


# ---------------------------------------------------------------------------
# Section 3 — Context-menu integration tests (real main fixture)
# ---------------------------------------------------------------------------


def test_empty_space_menu_contains_stage_nonlocal(qtbot, main):
    """
    Right-clicking whitespace in the project tree must produce a menu that
    includes 'Stage non-local file'.
    """
    menu = main.sidebar.context_menu_maker._build_empty_space_menu()
    action_texts = [a.text() for a in menu.actions()]
    assert "Stage non-local file" in action_texts, (
        f"'Stage non-local file' must be in the empty-space menu; got {action_texts}"
    )


def test_stage_nonlocal_action_is_callable(qtbot, main):
    """
    sidebar.actions must have a callable _stage_nonlocal_data method that
    the context menu action triggers.
    """
    assert hasattr(main.sidebar.actions, "_stage_nonlocal_data")
    assert callable(main.sidebar.actions._stage_nonlocal_data)


def test_sidebar_exposes_do_stage_nonlocal(qtbot, main):
    """
    sidebar must expose do_stage_nonlocal() so StageNonLocalDialog can
    register files after download/copy.
    """
    assert hasattr(main.sidebar, "do_stage_nonlocal")
    assert callable(main.sidebar.do_stage_nonlocal)
