import os
import io
import hashlib

from PySide6.QtCore import Qt, Slot
from PySide6.QtWidgets import (
    QLineEdit,
    QFormLayout,
    QPushButton,
    QLabel,
    QScrollArea,
    QMessageBox,
)

from csvpath.util.file_writers import DataFileWriter
from csvpath.util.nos import Nos

from flightpath.util.api.server_api import FlightPathServerApi

from flightpath.util.message_utility import MessageUtility as meut
from flightpath.util.file_utility import FileUtility as fiut
from flightpath.util.os_utility import OsUtility as osut
from flightpath.util.deploy_utility import DeployUtility as deut

from flightpath.dialogs.compile_env_dialog import CompileEnvDialog
from flightpath.dialogs.sync_config_dialog import SyncConfigDialog
from flightpath.dialogs.new_key_dialog import NewKeyDialog
from .server_projects_list import ServerProjectsList
from .blank_form import BlankForm


class ServerForm(BlankForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        #
        # _api is the concrete implementation of the api version in use. it is alwas
        # the most recent version the server publishes that the client has available.
        # at this time it is not possible to set a FlightPath Data to support a
        # lower version of the api than the highest version it has an implementation
        # for.
        #
        self._api = None
        #
        # we want to only update the projects list when there is a change that hasn't
        # caused an update AND we're in view
        #
        layout = QFormLayout()

        self.host = QLineEdit()
        layout.addRow("Host with port: ", self.host)

        self.key = QLineEdit()
        layout.addRow("API key: ", self.key)

        self.create_new_key = QPushButton("Create new API key")
        layout.addRow("Create new key: ", self.create_new_key)

        self.shut_down_server = QPushButton("Shutdown FlightPath Server")
        layout.addRow("Shutdown server: ", self.shut_down_server)
        self._enable_server_if()

        self.proj_list = ServerProjectsList(self)
        layout.addRow("Projects for key: ", self.proj_list)

        self.projects_path_area = QScrollArea()
        self.projects_path_area.setWidgetResizable(True)
        self.projects_path_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.projects_path_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.projects_path_area.setFixedHeight(33)
        self.projects_path_area.setWidgetResizable(True)
        self.projects_path = QLabel()
        self.projects_path.setText("")
        self.projects_path.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.projects_path_area.setWidget(self.projects_path)

        layout.addRow("Key directory: ", self.projects_path_area)

        self.docs = QLabel()
        self.docs.setTextInteractionFlags(Qt.LinksAccessibleByMouse)
        self.docs.setOpenExternalLinks(True)

        self.docs_link_area = QScrollArea()
        self.docs_link_area.setWidgetResizable(True)
        self.docs_link_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.docs_link_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.docs_link_area.setFixedHeight(33)
        self.docs_link_area.setWidgetResizable(True)
        self.docs_link_area.setWidget(self.docs)

        layout.addRow("Server API docs: ", self.docs_link_area)

        self.setLayout(layout)
        self._setup()

        self.main.config.config_panel.forms_layout.currentChanged.connect(
            self.on_widget_changed
        )
        #
        # if we haven't been viewed we won't have loaded the server and key fields
        #
        self.server_unchanged = False
        self.viewed = False

    @property
    def hostname(self) -> str:
        host = self.host.text()
        if host is None:
            return None
        host = host.strip()
        host = host.rstrip("/")
        return host

    def _is_on_top(self) -> bool:
        if self.main.config:
            i = self.main.config.config_panel.forms_layout.currentIndex()
            return i == 11
        return False

    @property
    def section(self) -> str:
        return "server"

    def on_widget_changed(self) -> None:
        #
        # watches for when a new form becomes visibile. if it is us, we want to check the
        # projects list
        #
        if self.main.config.config_panel.forms_layout.currentWidget() == self:
            self.populate()
            self._update_project_list()
            self.server_unchanged = True
            self.viewed = True

    def _set_projects_path(self) -> None:
        key = self.key.text()
        if key is None:
            self.projects_path.setText("")
            return
        key = key.strip()
        if key == "":
            self.projects_path.setText("")
            return
        hashstr = hashlib.sha256(key.encode()).hexdigest()
        self.projects_path.setText(hashstr)

    def add_to_config(self, config) -> None:
        #
        # if we've never been viewed we won't have setup the host and key.
        # if we don't do that and save we'll be saving blanks.
        #
        self.populate_if()
        host = self.hostname
        key = self.key.text()
        config.add_to_config("server", "host", host)
        config.add_to_config("server", "api_key", key)
        self._enable_server_if()

    def _server_is_enabled(self) -> bool:
        host = self.hostname
        key = self.key.text()
        e = True if host and host.strip() != "" else False
        e = True if e and key and key.strip() != "" else False
        return e and self._enableable()

    def _enable_server_if(self) -> None:
        if self._server_is_enabled():
            self._enable_shutdown_server()
        else:
            self._disable_shutdown_server()

    def _disable_shutdown_server(self) -> None:
        self.shut_down_server.setEnabled(False)
        self.shut_down_server.setText("Server is not accessible")

    def _enable_shutdown_server(self) -> None:
        self.shut_down_server.setEnabled(True)
        self.shut_down_server.setText("Shutdown FlightPath Server")

    def _setup(self) -> None:
        self.host.textChanged.connect(self.main.reactor.on_config_changed)
        self.host.textChanged.connect(self._update_project_list_new_host)

        self.key.textChanged.connect(self.main.reactor.on_config_changed)
        self.key.textChanged.connect(self._set_projects_path)
        self.key.textChanged.connect(self._update_project_list_new_key)

        self.shut_down_server.clicked.connect(self._do_shutdown)
        self.create_new_key.clicked.connect(self._create_key)

    def populate(self):
        if self.main.config.config_panel.forms_layout.currentWidget() != self:
            return
        if self.server_unchanged is True:
            return
        self.really_populate()

    def populate_if(self) -> None:
        #
        # if we never setup or never viewed we have to do a populate()
        # server unchanged will always be false if viewed is false. but in principle
        # we could set the values and never show them.
        #
        if self.viewed is False:
            self.really_populate()

    def really_populate(self) -> None:
        en = self.main.config.toolbar.button_close.isEnabled()
        config = self.config
        host = config.get(
            section="server", name="host", string_parse=False, swaps=False
        )
        if host and self.hostname != host:
            host = host.rstrip("/")
            self.host.setText(host)
            self.server_unchanged = False
        key = config.get(
            section="server", name="api_key", string_parse=False, swaps=False
        )

        if key and self.key.text() != key:
            self.key.setText(key)
            self.server_unchanged = False
        self._enable_server_if()
        if en:
            self.main.config.reset_config_toolbar()

        link = self.hostname
        if str(link).strip() not in ["None", ""]:
            self.docs.setText(f'<a href="{link}/docs">{link}/docs</a>')
        else:
            self.docs.setText("")
        self._update_project_list(name=None)

    @property
    def _headers(self) -> str:
        headers = {"access_token": self.key.text()}
        return headers

    def _enableable(self, *, host=None, key=None) -> bool:
        host = host if host else self.hostname
        key = key if key else self.key.text()
        e = True if host and host.strip() != "" else False
        e = True if e and key and key.strip() != "" else False
        if e is True:
            e = self._ping() == 200
        return e

    def _create_config_str(self, name: str) -> str:
        self.main.save_config_changes()
        config = self.main.csvpath_config._config
        string_buffer = io.StringIO()
        config.write(string_buffer)
        config_str = string_buffer.getvalue()
        #
        # the server will do a bunch of mods to the config we send. we
        # probably should do some here, but at least we're safe.
        #
        return config_str

    def _update_project_list_new_host(self) -> None:
        text = self.hostname
        if text and text.strip() == "":
            self.proj_list.clear()
        else:
            self.server_unchanged = False
            self._update_project_list()

    def _update_project_list_new_key(self) -> None:
        text = self.key.text()
        if text and text.strip() == "":
            self.proj_list.clear()
        else:
            self.server_unchanged = False
            self._update_project_list()

    def _update_project_list(self, name=None) -> None:
        key = self.key.text().strip() if self.key.text() else None
        host = self.hostname if self.hostname else None
        if key in [None, ""] or host in ["", None]:
            self.proj_list.clear()
            self.server_unchanged = False
            return
        #
        # repopulate only if we're visible. we'll repopulate each time we become visible.
        #
        if self.main.config.config_panel.forms_layout.currentWidget() != self:
            return
        if self.server_unchanged is True:
            return
        if not self._server_is_enabled():
            return

        self.proj_list.clear()
        names = self._get_project_names()
        if names is None:
            raise ValueError("Project names list cannot be None")
        for n in names:
            self.proj_list.addItem(n)
        if len(names) > 0:
            if name is not None:
                self.proj_list.select_item_by_name(name)
            else:
                item = self.proj_list.item(0)
                if item:
                    self.proj_list.setCurrentItem(item)

        self.server_unchanged = True

    def _write_to(self, name: str, content: str) -> None:
        to_index = self.main.sidebar.file_navigator.currentIndex()
        to_path = None
        if to_index.isValid():
            to_path = self.main.sidebar.proxy_model.filePath(to_index)
        else:
            to_path = self.main.state.cwd
        to_nos = Nos(to_path)
        if to_nos.isfile():
            to_path = os.path.dirname(to_path)
            to_nos = Nos(to_path)
        to_path = fiut.deconflicted_path(to_path, name)
        to_nos.path = to_path
        if to_nos.exists():
            raise RuntimeError(f"Path cannot exist: {to_nos.path}")
        with DataFileWriter(path=to_path) as tto:
            tto.write(content)
        return to_path

    @Slot(int)
    def _open_if(self, answer: int, *, path: str) -> None:
        if answer == QMessageBox.Yes:
            osut.open_file(path)

    # ====================
    # api calls
    # ====================

    @property
    def api(self):
        if self._api is None:
            key = self.key.text()
            if str(key).strip() not in ["", "None"]:
                self._api = FlightPathServerApi(self.hostname)
                self._api.key = key
            else:
                raise ValueError("No API key available")
        return self._api

    def _upload_env(self, name: str) -> bool:
        if not self._server_is_enabled():
            meut.warning2(
                parent=self,
                msg="Cannot upload env JSON because the server is off or there is insufficient information to make the request",
            )
            return
        #
        # open a dialog to collect the env vars
        #
        env_dialog = CompileEnvDialog(parent=self, main=self.main, name=name)
        env_dialog.show_dialog()
        env_str = env_dialog.config_str
        if env_str is None:
            return False
        #
        #
        #
        result = self.api.upload_env(name, env_str)
        if result.success is True:
            return True
        msg = f"Cannot upload env. Server response: {result.error}"
        meut.warning2(parent=self, title="Cannot upload env JSON", msg=msg)
        return False

    def _sync_config(self, name: str) -> None:
        d = SyncConfigDialog(main=self.main, name=name, parent=self)
        d.show_dialog()

    def _upload_config(
        self, name: str, config_str: str = None, *, prompt: bool = True
    ) -> None:
        if not self._server_is_enabled():
            meut.warning2(
                parent=self,
                msg="Cannot upload config because the server is off or there is insufficient information to make the request",
            )
            return
        #
        # for uploads, mainly, we want to prompt. with syncs there is less of a need
        # to prompt because the process is more visual and under the control of the
        # user.
        #
        if prompt:
            meut.yesNo2(
                parent=self,
                title="Overwrite project config?",
                msg=f"Permanently overwrite the {name} project's config?",
                callback=self._upload_config_answer,
                args={"name": name, "config_str": config_str},
            )
            return
        else:
            self._upload_config_answer(
                QMessageBox.Yes, name=name, config_str=config_str
            )

    def _upload_config_answer(
        self, answer: int, *, name: str, config_str: str = None
    ) -> None:
        if answer == QMessageBox.No:
            return

        if config_str is None:
            config_str = self._create_config_str(name)
        config_str = deut.make_deployable(config_str)

        result = self.api.upload_config(name, config_str)
        if result.success:
            return
        else:
            msg = "" if result.error_message is None else result.error_message
            msg = f"Cannot upload config. {msg} ({result.status_code})"
            meut.warning2(parent=self, title="Cannot upload config", msg=msg)

    #
    # api is used in create key dialog
    #
    def _create_key(self) -> None:
        new_key_dialog = NewKeyDialog(
            parent=self, failed_callback=self._create_key_failed
        )
        new_key_dialog.show()

    def _create_key_failed(self, msg, code) -> None:
        if code is None or code <= 100:
            code = 500
        meut.warning2(parent=self, title=f"{code}: Cannot create new API key", msg=msg)

    def _do_shutdown(self) -> None:
        if not self._server_is_enabled():
            meut.warning2(
                parent=self,
                msg="Cannot shutdown because the server is off or there is insufficient information to make the request",
            )
            return
        meut.yesNo2(
            parent=self,
            msg="Shutdown server?",
            title="Shutdown server?",
            callback=self._do_shutdown_answer,
        )

    def _do_shutdown_answer(self, answer: int) -> None:
        if answer == QMessageBox.No:
            return False
        result = self.api.shutdown()
        if result.success:
            msg = (
                result.data["message"]
                if "message" in result.data
                else result.data["detail"]
            )
            self._disable_shutdown_server()
            self.proj_list.clear()
        else:
            msg = f"Error sending request: {result.error_message}"
            meut.warning2(parent=self, title="Request Error", msg=msg)

    def _download_log(self, name: str) -> None:
        if not self._server_is_enabled():
            meut.warning2(
                parent=self,
                msg="Cannot download log because the server is off or there is insufficient information to make the request",
            )
            return False
        result = self.api.download_log(name)
        if result.success:
            local_path = self._write_to("csvpath.log", result.data)
            self.main.statusBar().showMessage(f"Saved to {local_path}")
            meut.yesNo2(
                parent=self,
                title="Open file?",
                msg=f"Open {local_path}?",
                callback=self._open_if,
                args={"path": local_path},
            )
        else:
            msg = result.error_message
            msg = "" if msg is None else msg
            msg = f"Cannot download log. {msg} ({result.status_code})"
            meut.warning2(parent=self, title="Cannot download log", msg=msg)

    def _download_config(self, name: str) -> None:
        if not self._server_is_enabled():
            meut.warning2(
                parent=self,
                msg="Cannot download config because the server is off or there is insufficient information to make the request",
            )
            return
        result = self.api.download_config(name)
        if result.success:
            local_path = self._write_to("config.ini", result.data)
            self.main.statusBar().showMessage(f"Saved to {local_path}")
            meut.yesNo2(
                parent=self,
                title="Open file?",
                msg=f"Open {local_path}?",
                callback=self._open_if,
                args={"path": local_path},
            )
            return
        else:
            msg = result.error_message
            msg = "" if msg is None else msg
            msg = f"Cannot download log. {msg} ({result.status_code})"
            meut.warning2(parent=self, title="Cannot download log", msg=msg)

    def _download_env(self, name: str) -> None:
        if not self._server_is_enabled():
            meut.warning2(
                parent=self,
                msg="Cannot download env file because the server is off or there is insufficient information to make the request",
            )
            return
        result = self.api.download_env(name)
        if result.success:
            local_path = self._write_to("env.json", result.data)
            self.main.statusBar().showMessage(f"Saved to {local_path}")
            meut.yesNo2(
                parent=self,
                title="Open file?",
                msg=f"Open {local_path}?",
                callback=self._open_if,
                args={"path": local_path},
            )
            return
        else:
            msg = result.error_message
            msg = "" if msg is None else msg
            msg = f"Cannot download log. {msg}. ({result.status_code})"
            meut.warning2(parent=self, title="Cannot download env", msg=msg)

    def _get_project_names(self) -> list[str]:
        if not self._server_is_enabled():
            if self._is_on_top():
                meut.warning2(
                    parent=self,
                    msg="Cannot get project names because the server is off or the request is incomplete",
                )
            return []
        result = self.api.get_project_names()
        if result.success:
            return result.data
        else:
            msg = "" if result.error_message is None else result.error_message
            msg = f"Error sending request. {msg} ({result.status_code})"
            meut.warning2(parent=self, title="Request Error", msg=msg)
        return []

    def _delete_project(self, name: str) -> bool:
        if not self._server_is_enabled():
            meut.warning2(
                parent=self,
                msg="Cannot delete project because the server is off or there is insufficient information to make the request",
            )
            return
        meut.yesNo2(
            parent=self,
            msg=f"Permanently delete project {name}?",
            title="Delete Project",
            callback=self._delete_project_answer,
            args={"name": name},
        )

    def _delete_project_answer(self, answer: int, *, name: str) -> None:
        if answer != QMessageBox.Yes:
            return False
        result = self.api.delete_project(name)
        if result.success:
            self.server_unchanged = False
            self._update_project_list()
            return
        else:
            meut.warning2(parent=self, title="Request Error", msg=result.error_message)

    def _create_project(self, name: str) -> bool:
        if not self._server_is_enabled():
            meut.warning2(
                parent=self,
                msg="Cannot create project because the server is off or there is insufficient information to make the request",
            )
            return False
        config_str = self._create_config_str(name)
        result = self.api.create_project(name, config_str)
        if result.success:
            self.server_unchanged = False
            self._update_project_list(name)
        else:
            msg = "" if result.error_message is None else result.error_message
            meut.warning2(
                parent=self,
                msg=f"Could not create project. {msg} ({result.status_code}) ",
                title="Could not create project",
            )

    def _ping(self) -> int:
        if self.hostname is None or self.hostname == "":
            return 400
        result = self.api.ping(self.hostname)
        return result.status_code if result.success else 500
