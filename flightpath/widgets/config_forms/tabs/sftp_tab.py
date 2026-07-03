from PySide6.QtCore import QThreadPool
from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QFormLayout,
)

from flightpath.util.message_utility import MessageUtility as meut
from flightpath.workers.sftp_test_worker import SftpTestWorker


class SftpTab(QWidget):
    def __init__(self, form):
        super().__init__(form)
        self.form = form

        layout = QFormLayout()
        self.setLayout(layout)

        self.server = QLineEdit()
        layout.addRow("Server: ", self.server)

        self.port = QLineEdit()
        layout.addRow("Port: ", self.port)

        self.username = QLineEdit()
        layout.addRow("Username: ", self.username)

        self.password = QLineEdit()
        layout.addRow("Password: ", self.password)

        buttons = QWidget()
        buttons_layout = QHBoxLayout()
        buttons.setLayout(buttons_layout)
        self.test_button = QPushButton("Test Connection")
        self.test_button.clicked.connect(self.test_connection)
        buttons_layout.addWidget(self.test_button)
        layout.addRow(buttons)

        self.server.textChanged.connect(self.form.main.reactor.on_config_changed)
        self.port.textChanged.connect(self.form.main.reactor.on_config_changed)
        self.username.textChanged.connect(self.form.main.reactor.on_config_changed)
        self.password.textChanged.connect(self.form.main.reactor.on_config_changed)

    def test_connection(self) -> None:
        server = self.server.text().strip()
        if not server:
            meut.message2(
                parent=self,
                title="Missing server",
                msg="Enter a server address before testing the connection.",
            )
            return
        port_text = self.port.text().strip()
        try:
            port = int(port_text) if port_text else 22
        except ValueError:
            port = 22
        username = self.username.text().strip()
        password = self.password.text()
        self.test_button.setEnabled(False)
        self.test_button.setText("Testing…")
        worker = SftpTestWorker(
            server=server, port=port, username=username, password=password
        )
        worker.signals.finished.connect(self.on_test_result)
        QThreadPool.globalInstance().start(worker)

    def on_test_result(self, success: bool, message: str) -> None:
        self.test_button.setEnabled(True)
        self.test_button.setText("Test Connection")
        title = "Connection Successful" if success else "Connection Failed"
        icon = QMessageBox.Information if success else QMessageBox.Warning
        meut.message2(parent=self, title=title, msg=message, icon=icon)

    @property
    def section(self) -> str:
        return "sftp"

    @property
    def server_fields(self) -> list[str]:
        return ["server", "port", "username", "password"]

    @property
    def server_fields_count(self) -> int:
        return len(self.server_fields)

    def add_to_config(self, config) -> None:
        server = self.server.text()
        self.form.config.add_to_config(self.section, "server", server)

        port = self.port.text()
        self.form.config.add_to_config(self.section, "port", port)

        username = self.username.text()
        self.form.config.add_to_config(self.section, "username", username)

        password = self.password.text()
        self.form.config.add_to_config(self.section, "password", password)

    def populate(self):
        config = self.form.config
        server = config.get(
            section=self.section,
            name="server",
            default="",
            string_parse=False,
            swaps=False,
        )
        self.server.setText(server)

        port = config.get(
            section=self.section,
            name="port",
            default="",
            string_parse=False,
            swaps=False,
        )
        self.port.setText(port)

        username = config.get(
            section=self.section,
            name="username",
            default="",
            string_parse=False,
            swaps=False,
        )
        self.username.setText(username)

        password = config.get(
            section=self.section,
            name="password",
            default="",
            swaps=False,
            string_parse=False,
        )
        self.password.setText(password)
