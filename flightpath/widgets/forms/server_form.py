import io
import base64
import httpx
from PySide6.QtWidgets import (
    QWidget,
    QLineEdit,
    QFormLayout,
    QComboBox,
    QPushButton,
    QLabel,
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
from flightpath.dialogs.new_key_dialog import NewKeyDialog
from .server_projects_list import ServerProjectsList
from .blank_form import BlankForm

class ServerForm(BlankForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        layout = QFormLayout()

        self.host = QLineEdit()
        layout.addRow("host with port: ", self.host)

        self.key = QLineEdit()
        layout.addRow("API key: ", self.key)

        self.create_new_key = QPushButton("Create new API key")
        layout.addRow("Create new key: ", self.create_new_key)

        self.shut_down_server = QPushButton("Shutdown FlightPath Server")
        layout.addRow("Shutdown server: ", self.shut_down_server)

        self.response_msg = QLabel("")
        self.response_msg.setStyleSheet("QLabel { font-size: 14pt;color:#222222;}")
        layout.addRow("", self.response_msg)

        self.proj_list = ServerProjectsList(self)
        layout.addRow("Projects for key: ", self.proj_list)

        self.setLayout(layout)
        self._setup()

    def add_to_config(self, config) -> None:
        host = self.host.text()
        key = self.key.text()
        config.add_to_config("server", "host", host )
        config.add_to_config("server", "api_key", key )

        e = True if host and host.strip() != "" else False
        e = True if e and key and key.strip() != "" else False
        self.shut_down_server.setEnabled(self._enableable())

    def _setup(self) -> None:
        self.host.textChanged.connect(self.main.on_config_changed)
        self.key.textChanged.connect(self.main.on_config_changed)
        self.shut_down_server.clicked.connect(self._do_shutdown)
        self.create_new_key.clicked.connect(self._create_key)

    def populate(self):
        config = self.config

        host = config.get(section="server", name="host")
        if host:
            self.host.setText(host)
        key = config.get(section="server", name="api_key")
        if key:
            self.key.setText(key)

        self.shut_down_server.setEnabled(self._enableable(host=host, key=key))
        self.response_msg.setText("")

        if key:
            self._update_project_list()

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
        config = self.main.csvpath_config
        config = config._config
        string_buffer = io.StringIO()
        config.write(string_buffer)
        config_str = string_buffer.getvalue()
        #
        # the server will do a bunch of mods to the config we send. we
        # probably should do some here, but at least we're safe.
        #
        return config_str

    def _update_project_list(self) -> None:
        self.proj_list.clear()
        names = self._get_project_names()
        if names is None:
            raise RuntimeError("Could not refresh projects")
        for name in names:
            self.proj_list.addItem(name)
        if len(names) > 0:
            item = self.proj_list.item(0)
            if item:
                self.proj_list.setCurrentItem(item)

    def _write_to(self, name:str, content:str) -> None:
        to_index = self.main.sidebar.file_navigator.currentIndex()
        to_path = None
        if to_index.isValid():
            to_path = self.main.sidebar.proxy_model.filePath(to_index)
        else:
            to_path = self.main.state.cwd
        to_nos = Nos(to_path)
        if to_nos.isfile():
            to_nos.path = os.path.dirname(to_path)
        to_path = fiut.deconflicted_path(to_path, name)
        to_nos.path = to_path
        if to_nos.exists():
            raise RuntimeError(f"Path cannot exist: {to_nos.path}")
        print(f"writing to: {to_path}")
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
        if not self._enableable():
            meut.warning(
                parent=self,
                msg=f"Cannot upload env JSON because the server is off or there is insufficient information to make the request")
            return
        if meut.yes_no(
            parent=self,
            title="Overwrite project env JSON values?",
            msg=f"Permanently overwrite the {name} project's env JSON?"
        ) is False:
            return
        #
        # open a dialog to collect the env vars
        #
        print(f"opening CompileEnvDialog")
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
            print(f"setting to: {url}")
            try:
                response = client.post(url, json=request, headers=self._headers)
                print(f"response: {response}")
                if response.status_code == 200:
                    return True
                else:
                    msg = response.json()["detail"]
                    msg = f"Cannot upload env. Server response: {response.status_code}: {msg}"
                    meut.warning(parent=self, title="Cannot upload env JSON", msg=msg)
            except Exception as ex:
                import traceback
                print(traceback.format_exc())
                msg = f"Error sending request ({response.status_code}): {ex}"
                print(msg)
                return False



    def _upload_config(self, name:str) -> bool:
        if not self._enableable():
            meut.warning(
                parent=self,
                msg=f"Cannot upload config because the server is off or there is insufficient information to make the request")
            return
        if meut.yes_no(
            parent=self,
            title="Overwrite project config?",
            msg=f"Permanently overwrite the {name} project's config?"
        ) is False:
            return
        with httpx.Client() as client:
            msg = None
            response = None
            url = f"{self.host.text()}/projects/set_project_config"
            config_str = self._create_config_str(name)
            config_str = deut.make_deployable(config_str)
            #
            # create a server-safeish config str here. this isn't a full cleaning. the
            # server needs to also work on the paths and check the sensitive settings
            # but we don't want to send something we know is completely unconsidered to
            # the server environment.
            #
            request = {"name":name, "config_str": config_str}
            print(f"setting to: {url}")
            try:
                response = client.post(url, json=request, headers=self._headers)
                print(f"response: {response}")
                if response.status_code == 200:
                    return True
                else:
                    msg = response.json()["detail"]
                    msg = f"Cannot upload config. Server response: {response.status_code}: {msg}"
                    meut.warning(parent=self, title="Cannot upload config", msg=msg)
            except Exception as ex:
                import traceback
                print(traceback.format_exc())
                msg = f"Error sending request ({response.status_code}): {ex}"
                print(msg)
                return False

    def _create_key(self) -> None:
        new_key_dialog = NewKeyDialog(self)
        new_key_dialog.show()

    def _do_shutdown(self) -> None:
        if not self._enableable():
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
                print(f"shutting down server with: {url}")
                response = client.get(url, headers=self._headers)
                json = response.json()
                print(f"shutting down server response: {json}")
                msg = json["message"] if "message" in json else json["detail"]
                msg = f"Response: {response.status_code}: {msg}"
                self.shut_down_server.setEnabled(False)
            except Exception as ex:
                import traceback
                print(traceback.format_exc())
                msg = f"Error sending request: {ex}"
            self.response_msg.setText(msg)

    def _download_log(self, name:str) -> bool:
        if not self._enableable():
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
                print(f"getting log from: {url}")
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
                import traceback
                print(traceback.format_exc())
                msg = f"Error sending request ({response.status_code}): {ex}"
                print(msg)
                return False

    def _download_config(self, name:str) -> bool:
        if not self._enableable():
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
                print(f"getting from: {url}")
                response = client.post(url, json=request, headers=self._headers)
                print(f"response: {response}")
                content = response.json()
                print(f"content: {content}")
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
                import traceback
                print(traceback.format_exc())
                msg = f"Error sending request ({response.status_code}): {ex}"
                print(msg)
                return False

    def _download_env(self, name:str) -> bool:
        if not self._enableable():
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
                print(f"getting from: {url}")
                response = client.post(url, json=request, headers=self._headers)
                print(f"response: {response}")
                content = response.json()
                print(f"content: {content}")
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
                import traceback
                print(traceback.format_exc())
                msg = f"Error sending request ({response.status_code}): {ex}"
                print(msg)
                return False


    def _get_project_names(self) -> list[str]:
        if not self._enableable():
            meut.warning(
                parent=self,
                msg=f"Cannot download get project names because the server is off or there is insufficient information to make the request")
            return
        with httpx.Client() as client:
            msg = None
            response = None
            try:
                url = f"{self.host.text()}/projects/get_project_names"
                print(f"getting project names from: {url}")
                response = client.post(url, headers=self._headers)
                json = response.json()
                print(f"getting project names response: {json}")
                return json
            except Exception as ex:
                import traceback
                print(traceback.format_exc())
                msg = f"Error sending request ({response.status_code}): {ex}"
                print(msg)
                return []

    def _delete_project(self, name:str) -> bool:
        if not self._enableable():
            meut.warning(
                parent=self,
                msg=f"Cannot delete project because the server is off or there is insufficient information to make the request")
            return
        yn = meut.yesNo(parent=self, msg=f"Permanently delete project {name}?", title="Permanently delete?")
        if yn is False:
            return False
        with httpx.Client() as client:
            response = None
            try:
                url = f"{self.host.text()}/projects/delete_project"
                print(f"deleting project with: {url}")
                response = client.post(url, json={"name":name}, headers=self._headers)
                print(f"deleting project response: {response}")
                if response.status_code == 200:
                    self._update_project_list()
                    json = response.json()
                    meut.message(msg=f"Project {name} has been deleted", title="Deleted project")
                    return True
                else:
                    meut.message(msg=f"Could not delete project {name}. Return code: {response.status_code}", title="Could not delete project")
                    return False
            except Exception as ex:
                import traceback
                print(traceback.format_exc())
                msg = "Error sending request"
                if response:
                    msg = f"{msg} ({response.status_code}): {ex}"
                else:
                    msg = f"{msg}: {ex}"
                print(msg)
                return False

    def _create_project(self, name:str) -> bool:
        if not self._enableable():
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
                print(f"creating project with: {url}")
                response = client.post(url, json=project_data, headers=self._headers)
                print(f"creating project response: {response}")
                if response.status_code == 200:
                    self._update_project_list()
                    json = response.json()
                    meut.message(msg=json.get('message'), title="Created project")
                    return True
                else:
                    meut.message(msg=f"Could not create project. Return code: {response.status_code}", title="Could not create project")
                    return False
            except Exception as ex:
                import traceback
                print(traceback.format_exc())
                msg = "Error sending request"
                if response:
                    msg = f"{msg} ({response.status_code}): {ex}"
                else:
                    msg = f"{msg}: {ex}"
                print(msg)
                return False

    def _ping(self) -> int:
        with httpx.Client() as client:
            msg = None
            try:
                url = f"{self.host.text()}/"
                print(f"pinging server with: {url}")
                response = client.get(url, headers=self._headers)
                print(f"pinging server response: {response}")
                return response.status_code
            except Exception as ex:
                import traceback
                print(traceback.format_exc())
                return 500

