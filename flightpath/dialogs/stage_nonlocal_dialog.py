import os
import traceback
from urllib.parse import urlparse

from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtCore import Qt, QThreadPool

from csvpath.util.nos import Nos
from csvpath.util.file_readers import DataFileReader
from csvpath.util.file_writers import DataFileWriter

from flightpath.util.message_utility import MessageUtility as meut
from flightpath.util.file_utility import FileUtility as fiut
from flightpath.workers.sftp_test_worker import SftpTestWorker
from flightpath.workers.download_worker import DownloadWorker
from flightpath.dialogs.sftp_servers_dialog import SftpServersDialog


class StageNonLocalDialog(QDialog):
    """Stage a non-local (or out-of-project local) file as a named-file.

    Supports sftp://, s3://, azure://, gs:// URIs and local paths.
    For local paths outside the project the user may copy the file in;
    sftp:// URIs are always connection-validated before proceeding.
    """

    ALLOWED_PROTOCOLS = frozenset(["sftp://", "s3://", "azure://", "gs://"])

    def __init__(self, *, main, parent) -> None:
        super().__init__(None)
        self.sidebar = parent
        self.main = main
        self._uri_is_remote = False
        self._pending_stage = None  # (uri, name, dest, must_copy) stored when SFTP notice shows

        self.setWindowTitle("Stage Non-Local File")
        self.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint)
        self.setWindowModality(Qt.NonModal)
        # was setFixedWidth 660
        self.setMinimumWidth(860)
        #self.setMaximumHeight(300)

        form = QFormLayout()
        self.setLayout(form)

        self.named_file_name_ctl = QLineEdit()
        self.named_file_name_ctl.textChanged.connect(self._update_stage_button)
        form.addRow("Named-file name:", self.named_file_name_ctl)

        self.uri_ctl = QLineEdit()
        self.uri_ctl.setPlaceholderText(
            "sftp://host/path/file.csv  •  s3://bucket/key  •  /local/path/file.csv"
        )
        self.uri_ctl.textChanged.connect(self._on_uri_changed)
        form.addRow("File or URI:", self.uri_ctl)

        self.note_label = QLabel()
        self.note_label.setWordWrap(True)
        self.note_label.setStyleSheet("QLabel { color: #666; font-style: italic; }")
        self.note_label.setVisible(False)
        form.addRow("", self.note_label)

        # "Copy to project:" label; field side is [checkbox | dest text field]
        self.copy_label = QLabel("Copy to project:")
        self.copy_label.setVisible(False)

        self.copy_ctl = QCheckBox()
        self.copy_ctl.stateChanged.connect(self._on_copy_changed)

        self.dest_ctl = QLineEdit()
        self.dest_ctl.setPlaceholderText("e.g., inputs/external/")
        self.dest_ctl.textChanged.connect(self._on_dest_changed)
        self.dest_ctl.setVisible(False)

        copy_row = QWidget()
        copy_row_layout = QHBoxLayout()
        copy_row_layout.setContentsMargins(0, 0, 0, 0)
        copy_row_layout.addWidget(self.copy_ctl)
        copy_row_layout.addWidget(self.dest_ctl)
        copy_row.setLayout(copy_row_layout)
        self.copy_row = copy_row
        self.copy_row.setVisible(False)

        form.addRow(self.copy_label, self.copy_row)

        self.error_label = QLabel()
        self.error_label.setWordWrap(True)
        self.error_label.setStyleSheet("QLabel { color: #cc0000; }")
        self.error_label.setVisible(False)
        form.addRow("", self.error_label)

        # SFTP notice — shown instead of the red error when no SFTP server is
        # configured.  Provides two action buttons rather than just a message.
        self.sftp_notice = self._build_sftp_notice()
        form.addRow("", self.sftp_notice)

        self.stage_button = QPushButton("Stage")
        self.stage_button.setEnabled(False)
        self.stage_button.clicked.connect(self._on_stage_clicked)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)

        blay = QHBoxLayout()
        blay.setContentsMargins(0, 0, 0, 0)
        blay.addWidget(self.cancel_button)
        blay.addWidget(self.stage_button)
        form.addRow("", blay)

    def _build_sftp_notice(self) -> QWidget:
        """Build the non-blocking SFTP-not-configured notice with action buttons."""
        notice_label = QLabel(
            "You must configure an SFTP server before using it."
        )
        notice_label.setWordWrap(True)
        notice_label.setStyleSheet("QLabel { color: #1a5276; font-style: italic; }")
        self.sftp_notice_label = notice_label

        self.sftp_configure_button = QPushButton("Configure project-wide SFTP")
        self.sftp_configure_button.clicked.connect(self._on_configure_sftp_clicked)

        self.sftp_add_button = QPushButton("Stage SFTP file")
        self.sftp_add_button.setEnabled(False)
        self.sftp_add_button.clicked.connect(self._on_add_sftp_named_file_clicked)

        btn_row = QHBoxLayout()
        btn_row.setContentsMargins(0, 0, 0, 0)
        btn_row.addWidget(self.sftp_configure_button)
        btn_row.addWidget(self.sftp_add_button)

        vlay = QVBoxLayout()
        vlay.setContentsMargins(0, 4, 0, 0)
        vlay.addWidget(notice_label)
        vlay.addLayout(btn_row)

        container = QWidget()
        container.setLayout(vlay)
        container.setVisible(False)
        return container

    # -----------------------------------------------------------------------
    # URI plausibility
    # -----------------------------------------------------------------------

    @staticmethod
    def _is_plausible_uri(text: str) -> bool:
        """Return True if text looks like a plausible remote URI.

        Requires at minimum protocol://host-or-bucket/some-path — two
        non-empty segments after the scheme separator.
        """
        if "://" not in text:
            return False
        rest = text.split("://", 1)[1]
        parts = [p for p in rest.split("/") if p.strip()]
        return len(parts) >= 2

    @staticmethod
    def _parse_sftp_host_port(uri: str) -> tuple[str, int]:
        """Return (hostname, port) parsed from an sftp:// URI.

        Port defaults to 22 when absent.
        """
        parsed = urlparse(uri)
        return parsed.hostname or "", parsed.port or 22

    # -----------------------------------------------------------------------
    # URI field change handler
    # -----------------------------------------------------------------------

    def _on_uri_changed(self, text: str) -> None:
        text = text.strip()
        self._uri_is_remote = False
        self._clear_error()

        if not text:
            self._hide_copy_controls()
            self.note_label.setVisible(False)
            self._update_stage_button()
            return

        if "://" in text:
            protocol = text.split("://")[0] + "://"
            if protocol in self.ALLOWED_PROTOCOLS:
                self._uri_is_remote = True
                self._show_copy_row_checked()
                self.note_label.setVisible(False)
            else:
                self._hide_copy_controls()
                self.note_label.setText(
                    f"Unsupported protocol '{protocol}'. "
                    "Use sftp://, s3://, azure://, or gs://."
                )
                self.note_label.setVisible(True)
        else:
            abs_path = os.path.abspath(text)
            if not Nos(abs_path).isfile():
                self._hide_copy_controls()
                self.note_label.setText("File not found.")
                self.note_label.setVisible(True)
            elif abs_path.startswith(self.main.state.cwd):
                self._hide_copy_controls()
                self.note_label.setText(
                    "This file is in your project and will be registered directly."
                )
                self.note_label.setVisible(True)
            else:
                self._show_copy_row_checked()
                self.note_label.setVisible(False)

        self._update_stage_button()
        self.adjustSize()

    def _show_copy_row_checked(self) -> None:
        """Show the copy row and default the checkbox to checked."""
        self.copy_label.setVisible(True)
        self.copy_row.setVisible(True)
        if not self.copy_ctl.isChecked():
            self.copy_ctl.setChecked(True)

    def _on_copy_changed(self) -> None:
        self.dest_ctl.setVisible(self.copy_ctl.isChecked())
        self._update_stage_button()
        self.adjustSize()

    def _on_dest_changed(self, text: str) -> None:
        if text.strip() and not self.copy_ctl.isChecked():
            self.copy_ctl.setChecked(True)
        self._update_stage_button()

    def _hide_copy_controls(self) -> None:
        self.copy_label.setVisible(False)
        self.copy_row.setVisible(False)
        self.copy_ctl.setChecked(False)
        self.dest_ctl.setVisible(False)

    # -----------------------------------------------------------------------
    # Stage button state
    # -----------------------------------------------------------------------

    def _update_stage_button(self) -> None:
        name = self.named_file_name_ctl.text().strip()
        uri = self.uri_ctl.text().strip()

        self.sftp_add_button.setEnabled(bool(name))

        if not uri or not name:
            self.stage_button.setEnabled(False)
            return

        if "://" in uri:
            protocol = uri.split("://")[0] + "://"
            if protocol not in self.ALLOWED_PROTOCOLS or not self._is_plausible_uri(uri):
                self.stage_button.setEnabled(False)
                return
        else:
            if not Nos(os.path.abspath(uri)).isfile():
                self.stage_button.setEnabled(False)
                return

        if self.copy_ctl.isChecked():
            self.stage_button.setEnabled(bool(self.dest_ctl.text().strip()))
        else:
            self.stage_button.setEnabled(True)

    # -----------------------------------------------------------------------
    # Stage click and validation
    # -----------------------------------------------------------------------

    def _on_stage_clicked(self) -> None:
        self._clear_error()
        uri = self.uri_ctl.text().strip()
        name = self.named_file_name_ctl.text().strip()

        if not uri or not name:
            self._show_error("Enter a file path or URI and a named-file name.")
            return

        if "://" in uri:
            protocol = uri.split("://")[0] + "://"
            if protocol not in self.ALLOWED_PROTOCOLS:
                self._show_error(
                    "Unsupported protocol. Use sftp://, s3://, azure://, or gs://."
                )
                return
            self._uri_is_remote = True
        else:
            abs_path = os.path.abspath(uri)
            if not Nos(abs_path).isfile():
                self._show_error("File not found.")
                return

        if self.copy_row.isVisible() and not self.copy_ctl.isChecked():
            meut.yesNo2(
                parent=self,
                title="Register without copying",
                msg="Register file without adding it to your project?",
                callback=self._on_confirm_register_without_copy,
                args={"uri": uri, "name": name},
            )
            return

        must_copy = self.copy_ctl.isChecked()
        dest = self.dest_ctl.text().strip() if must_copy else ""

        if must_copy and not dest:
            self._show_error("Enter a project-relative destination path.")
            return

        if uri.startswith("sftp://"):
            self._start_sftp_check(uri, name, dest, must_copy)
        else:
            self._proceed(uri, name, dest, must_copy)

    def _on_confirm_register_without_copy(self, answer, *, uri: str, name: str) -> None:
        if answer != QMessageBox.Yes:
            return
        if uri.startswith("sftp://"):
            self._start_sftp_check(uri, name, dest="", must_copy=False)
        else:
            self._proceed(uri, name, dest="", must_copy=False)

    def _proceed(self, uri: str, name: str, dest: str, must_copy: bool) -> None:
        if must_copy:
            local_path = self._resolve_local_path(uri, dest)
            if os.path.isdir(local_path):
                self._show_error(
                    f"'{os.path.basename(local_path)}' is an existing directory at "
                    "that location — choose a different destination name."
                )
                return
            if self._uri_is_remote:
                self._start_download(uri, local_path, name)
            else:
                self._copy_local(uri, local_path, name)
        else:
            self._register(uri, name)

    # -----------------------------------------------------------------------
    # SFTP validation
    # -----------------------------------------------------------------------

    def _check_sftp_config(self, host: str, name: str) -> tuple[bool, dict | None]:
        """Return (configured, credentials_or_None).

        (True,  creds) — host matched a known config; creds dict ready for SftpTestWorker
        (False, None)  — no matching config found; caller should show the notice/buttons
        """
        # --- 1. Project-wide SFTP in config.ini [sftp] section ---
        csvpath_config = self.main.csvpath_config
        server = str(csvpath_config.get(section="sftp", name="server") or "").strip()
        if server and server == host:
            port_raw = str(csvpath_config.get(section="sftp", name="port") or "").strip()
            try:
                port = int(port_raw) if port_raw else 22
            except ValueError:
                port = 22
            username = str(csvpath_config.get(section="sftp", name="username") or "").strip()
            password = str(csvpath_config.get(section="sftp", name="password") or "").strip()
            return True, {"server": server, "port": port, "username": username, "password": password}

        # --- 2. Per-named-file ServerConfig definitions ---
        file_manager = self.main.csvpaths.file_manager
        named_file_config = (
            file_manager.describer.get_config(name)
            if file_manager.has_named_file(name)
            else None
        )
        sources = named_file_config.sources if named_file_config and named_file_config.sources else {}
        for sc in sources.values():
            if sc.address == host:
                return True, {
                    "server": sc.address,
                    "port": sc.port if sc.port else 22,
                    "username": sc.username or "",
                    "password": sc.password or "",
                }

        # --- 3. No matching config found ---
        return False, None

    def _start_sftp_check(
        self, uri: str, name: str, dest: str, must_copy: bool
    ) -> None:
        host = urlparse(uri).hostname or ""
        any_sftp, creds = self._check_sftp_config(host, name)

        if not any_sftp:
            self._pending_stage = (uri, name, dest, must_copy)
            self._show_sftp_notice(host=host, name=name)
            return
        if creds is None:
            self._show_error(
                f"No SFTP server configured for '{host}'. "
                "Check Config > Integrations > SFTP."
            )
            return

        self.stage_button.setEnabled(False)
        self.stage_button.setText("Validating…")
        worker = SftpTestWorker(
            server=creds["server"],
            port=creds["port"],
            username=creds["username"],
            password=creds["password"],
        )
        worker.signals.finished.connect(
            lambda ok, msg: self._on_sftp_checked(ok, msg, uri, name, dest, must_copy)
        )
        QThreadPool.globalInstance().start(worker)

    def _on_sftp_checked(
        self, success: bool, message: str, uri: str, name: str, dest: str, must_copy: bool
    ) -> None:
        self._restore_stage_button()
        if not success:
            self._show_error(f"SFTP connection failed: {message}")
            return
        self._proceed(uri, name, dest, must_copy)

    # -----------------------------------------------------------------------
    # SFTP notice actions
    # -----------------------------------------------------------------------

    def _show_sftp_notice(self, *, host: str = "", name: str = "") -> None:
        """Show the informational SFTP notice, customized with host/name when available."""
        if host:
            self.sftp_notice_label.setText(
                f"You must configure the {host} server before using it."
            )
            self.sftp_add_button.setText(
                f"Add {host} to {name}" if name else "Stage SFTP file"
            )
        else:
            self.sftp_notice_label.setText(
                "You must configure an SFTP server before using it."
            )
            self.sftp_add_button.setText("Stage SFTP file")
        self.error_label.setVisible(False)
        self.sftp_notice.setVisible(True)
        self._update_stage_button()
        self.adjustSize()

    def _on_configure_sftp_clicked(self) -> None:
        """Navigate the main window to Config > Integrations (index 8)."""
        self.main.open_config()
        self.main.config.config_panel.forms_layout.setCurrentIndex(8)

    def _on_add_sftp_named_file_clicked(self) -> None:
        """Ensure named-file exists, check its SFTP configs, then either proceed
        (server already configured) or open SftpServersDialog to configure it."""
        name = self.named_file_name_ctl.text().strip()
        uri = self.uri_ctl.text().strip()
        if not name or not uri:
            return

        file_manager = self.main.csvpaths.file_manager

        # assure_named_file() is available from CsvPath Framework 0.0.618 onward.
        # Inline the two-line body here for compatibility with 0.0.617.
        if not file_manager.has_named_file(name):
            home = file_manager.assure_named_file_home(name)
            file_manager.registrar.manifest_path(home)

        config = file_manager.describer.get_config(name)
        configs = config.sources if config and config.sources else {}

        host, port = self._parse_sftp_host_port(uri)
        for server_config in configs.values():
            if server_config.address == host and server_config.port == port:
                # Named-file already has this server; no dialog needed — proceed to staging.
                self._clear_error()
                if self._pending_stage:
                    self._proceed(*self._pending_stage)
                    self._pending_stage = None
                return

        # Server not yet in named-file config — clear the notice first (comment #3),
        # then open SftpServersDialog to collect credentials.
        self._clear_error()
        self.sftp_sources_dialog = SftpServersDialog(
            parent=self,
            main=self.main,
            name=name,
            configs=configs,
        )
        self.sftp_sources_dialog.show_dialog()

    def set_sftps(self, name: str, configs) -> None:
        """Callback invoked by SftpServersDialog when the user saves.

        Persists the SFTP server configs for the named-file and auto-proceeds
        with the pending stage so the user doesn't need to click Stage again.
        """
        file_manager = self.main.csvpaths.file_manager
        config = file_manager.describer.get_config(name)
        config.sources = configs
        file_manager.describer.store_config(name, config)
        if self._pending_stage:
            self._proceed(*self._pending_stage)
            self._pending_stage = None

    # -----------------------------------------------------------------------
    # Copy / download
    # -----------------------------------------------------------------------

    def _resolve_local_path(self, uri: str, dest: str) -> str:
        source_filename = os.path.basename(uri.rstrip("/").split("?")[0])
        dest_clean = os.path.normpath(dest.lstrip("/"))
        _, dest_ext = os.path.splitext(os.path.basename(dest_clean))
        if dest_ext:
            # dest already names the target file (possibly with a different extension)
            return os.path.join(self.main.state.cwd, dest_clean)
        # dest is a directory; append source filename with deconfliction
        dest_dir = os.path.join(self.main.state.cwd, dest_clean)
        return fiut.deconflicted_path(dest_dir, source_filename)

    def _copy_local(self, src: str, local_path: str, name: str) -> None:
        try:
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            mode = "wb" if src.endswith(".xlsx") else "w"
            with DataFileReader(src) as reader:
                with DataFileWriter(path=local_path, mode=mode) as writer:
                    writer.write(reader.read())
            self._register(local_path, name)
        except Exception:
            self._show_exception("Copy failed")

    def _start_download(self, uri: str, local_path: str, name: str) -> None:
        self.stage_button.setEnabled(False)
        self.stage_button.setText("Downloading…")
        #
        # we may have either setup new SFTP backend or added ServerConfigs to
        # the named-file we're adding/using. because it might be the latter
        # we have to pull any configs and pass them along.
        #
        file_manager = self.main.csvpaths.file_manager
        config = file_manager.describer.get_config(name)
        configs = config.sources if config and config.sources else {}

        worker = DownloadWorker(uri=uri, local_path=local_path, configs=configs)
        worker.signals.finished.connect(
            lambda ok, result: self._on_downloaded(ok, result, name)
        )
        QThreadPool.globalInstance().start(worker)

    def _on_downloaded(self, success: bool, path_or_error: str, name: str) -> None:
        self._restore_stage_button()
        if not success:
            self._show_error(f"Download failed: {path_or_error}")
            return
        self._register(path_or_error, name)

    # -----------------------------------------------------------------------
    # Registration
    # -----------------------------------------------------------------------

    def _register(self, path: str, name: str) -> None:
        try:
            self.sidebar.do_stage_nonlocal(path=path, name=name)
            self.accept()
        except Exception:
            self._show_exception("Registration failed")

    # -----------------------------------------------------------------------
    # UI helpers
    # -----------------------------------------------------------------------

    def _restore_stage_button(self) -> None:
        self.stage_button.setText("Stage")
        self._update_stage_button()

    def _show_error(self, msg: str) -> None:
        self.sftp_notice.setVisible(False)
        self.error_label.setText(msg)
        self.error_label.setVisible(True)
        self.adjustSize()

    def _show_exception(self, title: str) -> None:
        """Show the current exception's full traceback in a popup.

        Avoids clipping the stack dump inside the dialog's bounded error label.
        """
        meut.message2(parent=self, title=title, msg=traceback.format_exc())

    def _clear_error(self) -> None:
        self.error_label.setVisible(False)
        self.sftp_notice.setVisible(False)

    def warning(self, msg: str, title: str) -> None:
        meut.warning2(parent=self, title=title, msg=msg)

    def show_dialog(self) -> None:
        self.show()
