from PySide6.QtWidgets import (
    QWidget,
    QLineEdit,
    QFormLayout,
    QLabel
)

class CkanTab(QWidget):
    def __init__(self, form):
        super().__init__()
        self.form = form
        layout = QFormLayout()
        self.setLayout(layout)

        self.server = QLineEdit()
        layout.addRow("Server: ", self.server)

        self.api_token = QLineEdit()
        layout.addRow("Api token: ", self.api_token)

        self.server.textChanged.connect(self.form.main.on_config_changed)
        self.api_token.textChanged.connect(self.form.main.on_config_changed)


    def add_to_config(self, config) -> None:
        server = self.server.text()
        self.form.config.add_to_config("ckan", "server", server )

        api_token = self.api_token.text()
        self.form.config.add_to_config("ckan", "api_token", api_token )

    def populate(self):
        config = self.form.config
        server = config.get(section="ckan", name="server", default="localhost:8443")
        self.server.setText(server)

        api_token = config.get(section="ckan", name="api_token", default="")
        self.api_token.setText(api_token)



