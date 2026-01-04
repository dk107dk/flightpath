from PySide6.QtWidgets import (
    QWidget,
    QLineEdit,
    QFormLayout,
    QLabel
)

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

        self.server.textChanged.connect(self.form.main.on_config_changed)
        self.port.textChanged.connect(self.form.main.on_config_changed)
        self.username.textChanged.connect(self.form.main.on_config_changed)
        self.password.textChanged.connect(self.form.main.on_config_changed)

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
        self.form.config.add_to_config(self.section, "port", port )

        username = self.username.text()
        self.form.config.add_to_config(self.section, "username", username )

        password = self.password.text()
        self.form.config.add_to_config(self.section, "password", password )


    def populate(self):
        config = self.form.config
        server = config.get(section=self.section, name="server", default="localhost")
        self.server.setText(server)

        port = config.get(section=self.section, name="port", default="22")
        self.port.setText(port)

        username = config.get(section=self.section, name="username", default="")
        self.username.setText(username)

        password = config.get(section=self.section, name="password", default="")
        self.password.setText(password)




