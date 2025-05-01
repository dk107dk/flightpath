from PySide6.QtWidgets import (
    QWidget,
    QLineEdit,
    QFormLayout,
    QLabel
)


class MarquezTab(QWidget):
    def __init__(self, form):
        super().__init__()
        self.form = form

        layout = QFormLayout()
        self.setLayout(layout)

        self.base_url = QLineEdit()
        layout.addRow("Base URL: ", self.base_url)

        self.endpoint = QLineEdit()
        layout.addRow("Endpoint: ", self.endpoint)

        self.api_key = QLineEdit()
        layout.addRow("Api key: ", self.api_key)

        self.timeout = QLineEdit()
        layout.addRow("Timeout: ", self.timeout)

        self.verify = QLineEdit()
        layout.addRow("Verify: ", self.verify)

        self.base_url.textChanged.connect(self.form.main.on_config_changed)
        self.endpoint.textChanged.connect(self.form.main.on_config_changed)
        self.api_key.textChanged.connect(self.form.main.on_config_changed)
        self.timeout.textChanged.connect(self.form.main.on_config_changed)
        self.verify.textChanged.connect(self.form.main.on_config_changed)


    def add_to_config(self, config) -> None:
        base_url = self.base_url.text()
        self.form.config.add_to_config("marquez", "base_url", base_url)

        endpoint = self.endpoint.text()
        self.form.config.add_to_config("marquez", "endpoint", endpoint )

        api_key = self.api_key.text()
        self.form.config.add_to_config("marquez", "api_key", api_key )

        timeout = self.timeout.text()
        self.form.config.add_to_config("marquez", "timeout", timeout )

        verify = self.verify.text()
        self.form.config.add_to_config("marquez", "verify", verify )


    def populate(self):
        config = self.form.config
        base_url = config.get(section="marquez", name="base_url", default="http://localhost:5000")
        self.base_url.setText(base_url)

        endpoint = config.get(section="marquez", name="endpoint", default="api/v1/lineage")
        self.endpoint.setText(endpoint)

        api_key = config.get(section="marquez", name="api_key", default="")
        self.api_key.setText(api_key)

        timeout = config.get(section="marquez", name="timeout", default="5")
        self.timeout.setText(timeout)

        verify = config.get(section="marquez", name="verify", default="False")
        self.verify.setText(verify)






