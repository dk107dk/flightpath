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


    def add_to_config(self, config) -> None:
        server = self.server.text()
        self.form.config.add_to_config("sftp", "server", server)

        port = self.port.text()
        self.form.config.add_to_config("sftp", "port", port )

        username = self.username.text()
        self.form.config.add_to_config("sftp", "username", username )

        password = self.password.text()
        self.form.config.add_to_config("sftp", "password", password )


    def populate(self):
        config = self.form.config
        server = config.get(section="sftp", name="server", default="localhost")
        self.server.setText(server)

        port = config.get(section="sftp", name="port", default="22")
        self.port.setText(port)

        username = config.get(section="sftp", name="username", default="")
        self.username.setText(username)

        password = config.get(section="sftp", name="password", default="")
        self.password.setText(password)




