from PySide6.QtWidgets import (
    QWidget,
    QLineEdit,
    QFormLayout,
    QLabel
)

class SftpPlusTab(QWidget):
    def __init__(self, form):
        super().__init__(form)
        self.form = form

        layout = QFormLayout()
        self.setLayout(layout)

        self.admin_username = QLineEdit()
        layout.addRow("Admin username: ", self.admin_username)

        self.admin_password = QLineEdit()
        layout.addRow("Admin password: ", self.admin_password)

        self.api_url = QLineEdit()
        layout.addRow("Api URL: ", self.api_url)

        self.scripts_dir = QLineEdit()
        layout.addRow("Scripts dir: ", self.scripts_dir)

        self.execute_timeout = QLineEdit()
        layout.addRow("Execute timeout: ", self.execute_timeout)

        self.mailbox_user = QLineEdit()
        layout.addRow("Mailbox user: ", self.mailbox_user)

        self.mailbox_password = QLineEdit()
        layout.addRow("Mailbox password: ", self.mailbox_password)

        self.server = QLineEdit()
        layout.addRow("Server: ", self.server)

        self.port = QLineEdit()
        layout.addRow("Port: ", self.port)

        self.admin_username.textChanged.connect(self.form.main.on_config_changed)
        self.admin_password.textChanged.connect(self.form.main.on_config_changed)
        self.api_url.textChanged.connect(self.form.main.on_config_changed)
        self.scripts_dir.textChanged.connect(self.form.main.on_config_changed)
        self.execute_timeout.textChanged.connect(self.form.main.on_config_changed)
        self.mailbox_user.textChanged.connect(self.form.main.on_config_changed)
        self.mailbox_password.textChanged.connect(self.form.main.on_config_changed)
        self.server.textChanged.connect(self.form.main.on_config_changed)
        self.port.textChanged.connect(self.form.main.on_config_changed)

    @property
    def section(self) -> str:
        return "sftpplus"

    @property
    def server_fields(self) -> list[str]:
        return []

    @property
    def server_fields_count(self) -> int:
        return len(self.server_fields)

    def add_to_config(self, config) -> None:
        admin_username = self.admin_username.text()
        self.form.config.add_to_config(self.section, "admin_username", admin_username)

        admin_password = self.admin_password.text()
        self.form.config.add_to_config(self.section, "admin_password", admin_password )

        api_url = self.api_url.text()
        self.form.config.add_to_config(self.section, "api_url", api_url )

        scripts_dir = self.scripts_dir.text()
        self.form.config.add_to_config(self.section, "scripts_dir", scripts_dir )

        execute_timeout = self.execute_timeout.text()
        self.form.config.add_to_config(self.section, "execute_timeout", execute_timeout)

        mailbox_user = self.mailbox_user.text()
        self.form.config.add_to_config(self.section, "mailbox_user", mailbox_user )

        mailbox_password = self.mailbox_password.text()
        self.form.config.add_to_config(self.section, "mailbox_password", mailbox_password )

        server = self.server.text()
        self.form.config.add_to_config(self.section, "server", server )

        port = self.port.text()
        self.form.config.add_to_config(self.section, "port", port )

    def populate(self):
        config = self.form.config
        admin_username = config.get(section=self.section, name="admin_username", default="SFTPPLUS_ADMIN_USERNAME")
        self.admin_username.setText(admin_username)

        admin_password = config.get(section=self.section, name="admin_password", default="SFTPPLUS_ADMIN_PASSWORD")
        self.admin_password.setText(admin_password)

        api_url = config.get(section=self.section, name="api_url", default="https://localhost:10020/json")
        self.api_url.setText(api_url)

        scripts_dir = config.get(section=self.section, name="scripts_dir", default="")
        self.scripts_dir.setText(scripts_dir)

        execute_timeout = config.get(section=self.section, name="execute_timeout", default="300")
        self.execute_timeout.setText(execute_timeout)

        mailbox_user = config.get(section=self.section, name="mailbox_user", default="mailbox")
        self.mailbox_user.setText(mailbox_user)

        mailbox_password = config.get(section=self.section, name="mailbox_password", default="SFTPPLUS_MAILBOX_PASSWORD")
        self.mailbox_password.setText(mailbox_password)

        server = config.get(section=self.section, name="server", default="SFTPPLUS_SERVER")
        self.server.setText(server)

        port = config.get(section=self.section, name="port", default="SFTPPLUS_PORT")
        self.port.setText(port)


