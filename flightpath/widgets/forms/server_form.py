import os
import io
import base64
import httpx
import hashlib
import traceback
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QLineEdit,
    QFormLayout,
    QComboBox,
    QPushButton,
    QLabel,
    QScrollArea,
    QListWidget
)
from csvpath.util.config import Config
from csvpath.util.file_writers import DataFileWriter
from csvpath.util.nos import Nos
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
        # we want to only update the projects list when there is a change that hasn't caused an update AND we're in view
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

        self.response_msg = QLabel("")
        self.response_msg.setStyleSheet("QLabel { font-size: 14pt;color:#222222;}")
        layout.addRow("", self.response_msg)

        self.proj_list = ServerProjectsList(self)
        layout.addRow("Projects for key: ", self.proj_list)

        self.projects_path_area = QScrollArea()
        self.projects_path_area.setWidgetResizable(True)
        self.projects_path_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.projects_path_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.projects_path_area.setFixedHeight(33)
        self.projects_path_area.setFixedWidth(384)
        self.projects_path = QLabel()
        self.projects_path.setText("")
        self.projects_path.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.projects_path_area.setWidget(self.projects_path)

        layout.addRow("Key directory: ", self.projects_path_area)

        self.setLayout(layout)
        self._setup()

        self.main.config.config_panel.forms_layout.currentChanged.connect(self.on_widget_changed)
        #
        # if we haven't been viewed we won't have loaded the server and key fields
        #
        self.server_unchanged = False
        self.viewed = False


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
        host = self.host.text()
        key = self.key.text()
        config.add_to_config("server", "host", host )
        config.add_to_config("server", "api_key", key )
        self._enable_server_if()

    def _server_is_enabled(self) -> bool:
        host = self.host.text()
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
        self.shut_down_server.setText("Server is not available")

    def _enable_shutdown_server(self) -> None:
        self.shut_down_server.setEnabled(True)
        self.shut_down_server.setText("Shutdown FlightPath Server")


    def _setup(self) -> None:
        self.host.textChanged.connect(self.main.on_config_changed)
        self.host.textChanged.connect(self._update_project_list_new_host)

        self.key.textChanged.connect(self.main.on_config_changed)
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
        host = config.get(section="server", name="host")
        if host and self.host.text() != host:
            self.host.setText(host)
            self.server_unchanged = False
        key = config.get(section="server", name="api_key")
        if key and self.key.text() != key:
            self.key.setText(key)
            self.server_unchanged = False
        self._enable_server_if()
        if en:
            self.main.config.reset_config_toolbar()


    @property
    def _headers(self) -> str:
        headers = {"access_token": self.key.text()}
        return headers

    def _enableable(self, *, host=None, key=None) -> bool:
        host = host if host else self.host.text()
        key = key if key else self.key.text()
        e = True if host and host.strip() != "" else False
        e = True if e and key and key.strip() != "" else False
        if e is True:
            e = self._ping() == 200
        return e

    def _create_config_str(self, name:str) -> str:
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
        text = self.host.text()
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
        host = self.host.text().strip() if self.host.text() else None
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


    def _write_to(self, name:str, content:str) -> None:
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

    def _open_if(self, path:str) -> None:
        if meut.yes_no(parent=self, title="Open file?", msg=f"Open {path}?") is True:
            osut.open_file(path)

#====================
# api calls
#====================

    def _upload_env(self, name:str) -> bool:
        if not self._server_is_enabled():
            meut.warning(
                parent=self,
                msg=f"Cannot upload env JSON because the server is off or there is insufficient information to make the request")
            return
        #
        # open a dialog to collect the env vars
        #
        env_dialog = CompileEnvDialog(parent=self, name=name)
        env_dialog.show_dialog()
        env_str = env_dialog.config_str
        if env_str is None:
            return False
        #
        #
        #
        with httpx.Client() as client:
            msg = None
            response = None
            url = f"{self.host.text()}/projects/set_env_file"
            #
            # create a server-safeish config str here. this isn't a full cleaning. the
            # server needs to also work on the paths and check the sensitive settings
            # but we don't want to send something we know is completely unconsidered to
            # the server environment.
            #
            request = {"name":name, "env_str": env_str}
            try:
                response = client.post(url, json=request, headers=self._headers)
                if response.status_code == 200:
                    return True
                else:
                    msg = response.json()
                    msg = ["detail"]
                    msg = f"Cannot upload env. Server response: {response.status_code}: {msg}"
                    meut.warning(parent=self, title="Cannot upload env JSON", msg=msg)
            except Exception as ex:
                print(traceback.format_exc())
                msg = f"Error sending request ({response.status_code}): {ex}"
                print(msg)
                return False


    def _sync_config(self, name:str) -> None:
        d = SyncConfigDialog(name=name, parent=self)
        d.show_dialog()

    def _upload_config(self, name:str, config_str:str=None, *, prompt:bool=True) -> bool:
        if not self._server_is_enabled():
            meut.warning(
                parent=self,
                msg=f"Cannot upload config because the server is off or there is insufficient information to make the request")
            return
        #
        # for uploads, mainly, we want to prompt. with syncs there is less of a need
        # to prompt because the process is more visual and under the control of the
        # user.
        #
        ok = True
        if prompt:
            ok = meut.yes_no(
                parent=self,
                title="Overwrite project config?",
                msg=f"Permanently overwrite the {name} project's config?"
            )
        if ok is False:
            return
        with httpx.Client() as client:
            msg = None
            response = None
            url = f"{self.host.text()}/projects/set_project_config"
            if config_str is None:
                config_str = self._create_config_str(name)

            cs = deut.make_deployable(config_str)
            config_str = cs
            #
            # create a server-safeish config str here. this isn't a full cleaning. the
            # server needs to also work on the paths and check the sensitive settings
            # but we don't want to send something we know is completely unconsidered to
            # the server environment.
            #
            request = {"name":name, "config_str": config_str}
            try:
                response = client.post(url, json=request, headers=self._headers)
                if response.status_code == 200:
                    return True
                else:
                    msg = response.json()["detail"]
                    msg = f"Cannot upload config. Server response: {response.status_code}: {msg}"
                    meut.warning(parent=self, title="Cannot upload config", msg=msg)
            except Exception as ex:
                msg = f"Error sending request ({response.status_code}): {ex}"
                return False



















    def _create_key(self) -> None:
        new_key_dialog = NewKeyDialog(self)
        new_key_dialog.show()

    def _do_shutdown(self) -> None:
        if not self._server_is_enabled():
            meut.warning(
                parent=self,
                msg=f"Cannot shutdown because the server is off or there is insufficient information to make the request")
            return
        yn = meut.yes_no(parent=self, msg=f"Shutdown server?", title="Shutdown server?")
        if yn is False:
            return False
        with httpx.Client() as client:
            msg = None
            try:
                url = f"{self.host.text()}/admin/shutdown"
                response = client.get(url, headers=self._headers)
                json = response.json()
                msg = json["message"] if "message" in json else json["detail"]
                msg = f"Response: {response.status_code}: {msg}"
                self._enable_server_if()
                #self.shut_down_server.setEnabled(False)
            except Exception as ex:
                msg = f"Error sending request: {ex}"
            self.response_msg.setText(msg)

    def _download_log(self, name:str) -> bool:
        if not self._server_is_enabled():
            meut.warning(
                parent=self,
                msg=f"Cannot download log because the server is off or there is insufficient information to make the request")
            return
        with httpx.Client() as client:
            msg = None
            response = None
            try:
                url = f"{self.host.text()}/projects/get_file"
                request = {"name":name, "file_path":"logs/csvpath.log"}
                response = client.post(url, json=request, headers=self._headers)
                json = response.json()
                if response.status_code == 200:
                    log = json.get("file_content")
                    log = base64.b64decode(log).decode('utf-8')
                    local_path = self._write_to("csvpath.log", log)
                    self.main.statusBar().showMessage(f"Saved to {local_path}")
                    self._open_if(local_path)
                    return True
                else:
                    msg = json["detail"]
                    msg = f"Cannot download log. Server response: {response.status_code}: {msg}"
                    meut.warning(parent=self, title="Cannot download log", msg=msg)
            except Exception as ex:
                print(traceback.format_exc())
                msg = f"Error sending request ({response.status_code}): {ex}"
                print(msg)
                return False

    def _download_config(self, name:str) -> bool:
        if not self._server_is_enabled():
            meut.warning(
                parent=self,
                msg=f"Cannot download config because the server is off or there is insufficient information to make the request")
            return
        with httpx.Client() as client:
            msg = None
            response = None
            try:
                url = f"{self.host.text()}/projects/get_project_config"
                request = {"name":name}
                response = client.post(url, json=request, headers=self._headers)
                content = response.json()
                if response.status_code == 200:
                    local_path = self._write_to("config.ini", content)
                    self.main.statusBar().showMessage(f"Saved to {local_path}")
                    self._open_if(local_path)
                    return True
                else:
                    msg = json["detail"]
                    msg = f"Cannot download log. Server response: {response.status_code}: {msg}"
                    meut.warning(parent=self, title="Cannot download log", msg=msg)
            except Exception as ex:
                print(traceback.format_exc())
                msg = f"Error sending request ({response.status_code}): {ex}"
                print(msg)
                return False

    def _download_env(self, name:str) -> bool:
        if not self._server_is_enabled():
            meut.warning(
                parent=self,
                msg=f"Cannot download env file because the server is off or there is insufficient information to make the request")
            return
        with httpx.Client() as client:
            msg = None
            response = None
            try:
                url = f"{self.host.text()}/projects/get_env_file"
                request = {"name":name}
                response = client.post(url, json=request, headers=self._headers)
                content = response.json()
                if response.status_code == 200:
                    local_path = self._write_to("env.json", content)
                    self.main.statusBar().showMessage(f"Saved to {local_path}")
                    self._open_if(local_path)
                    return True
                else:
                    msg = json["detail"]
                    msg = f"Cannot download log. Server response: {response.status_code}: {msg}"
                    meut.warning(parent=self, title="Cannot download env", msg=msg)
            except Exception as ex:
                print(traceback.format_exc())
                msg = f"Error sending request ({response.status_code}): {ex}"
                print(msg)
                return False

    def _is_on_top(self) -> bool:
        if self.main.config:
            i = self.main.config.config_panel.forms_layout.currentIndex()
            return i == 11
        return False

    def _get_project_names(self) -> list[str]:
        if not self._server_is_enabled():
            if self._is_on_top():
                meut.warning(
                    parent=self,
                    msg=f"Cannot get project names because the server is off or the request is incomplete")
            return []
        with httpx.Client() as client:
            msg = None
            response = None
            try:
                url = f"{self.host.text()}/projects/get_project_names"
                response = client.post(url, headers=self._headers)
                json = response.json()
                if "names" in json:
                    return json["names"]
                elif "detail" in json:
                    meut.warning( parent=self, msg=json["detail"], title="Error")
                else:
                    meut.warning( parent=self, msg=f"Could not complete the request: {json}", title="Error")
            except Exception as ex:
                print(traceback.format_exc())
                msg = f"Error sending request ({response.status_code}): {ex}"
                print(msg)
        return []

    def _delete_project(self, name:str) -> bool:
        if not self._server_is_enabled():
            meut.warning(
                parent=self,
                msg=f"Cannot delete project because the server is off or there is insufficient information to make the request")
            return
        yn = meut.yesNo(parent=self, msg=f"Permanently delete project {name}?", title="")
        if yn is False:
            return False
        with httpx.Client() as client:
            response = None
            try:
                url = f"{self.host.text()}/projects/delete_project"
                response = client.post(url, json={"name":name}, headers=self._headers)
                if response.status_code == 200:
                    json = response.json()
                    self.server_unchanged = False
                    self._update_project_list()
                    #
                    # the project list has to update and that should be enough
                    #
                    #meut.message(msg=f"Project {name} has been deleted", title="Deleted project")
                    return True
                else:
                    meut.message(msg=f"Could not delete project {name}. Return code: {response.status_code}", title="Could not delete project")
                    return False
            except Exception as ex:
                print(traceback.format_exc())
                msg = "Error sending request"
                if response:
                    msg = f"{msg} ({response.status_code}): {ex}"
                else:
                    msg = f"{msg}: {ex}"
                print(msg)
                return False

    def _create_project(self, name:str) -> bool:
        if not self._server_is_enabled():
            meut.warning(
                parent=self,
                msg=f"Cannot create project because the server is off or there is insufficient information to make the request")
            return
        with httpx.Client() as client:
            msg = None
            response = None
            try:
                config_str = self._create_config_str(name)
                project_data = {"name": name, "config_str": config_str}
                url = f"{self.host.text()}/projects/new_project"
                response = client.post(url, json=project_data, headers=self._headers)
                if response.status_code == 200:
                    self.server_unchanged = False
                    self._update_project_list(name)
                    json = response.json()
                    return True
                else:
                    meut.message(msg=f"Could not create project. Return code: {response.status_code}", title="Could not create project")
                    return False
            except Exception as ex:
                print(traceback.format_exc())
                msg = "Error sending request"
                if response:
                    msg = f"{msg} ({response.status_code}): {ex}"
                else:
                    msg = f"{msg}: {ex}"
                print(msg)
                return False

    def _ping(self) -> int:
        if self.host.text() is None or self.host.text().strip() == "":
            return 400
        with httpx.Client() as client:
            msg = None
            try:
                url = f"{self.host.text()}/"
                response = client.get(url, headers=self._headers)
                return response.status_code
            except Exception as ex:
                return 500

