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

    @property
    def section(self) -> str:
        return "openlineage"

    @property
    def server_fields(self) -> list[str]:
        return ["base_url", "endpoint", "api_key", "timeout", "verify"]

    @property
    def server_fields_count(self) -> int:
        return len(self.server_fields)


    def add_to_config(self, config) -> None:
        base_url = self.base_url.text()
        self.form.config.add_to_config(self.section, "base_url", base_url)

        endpoint = self.endpoint.text()
        self.form.config.add_to_config(self.section, "endpoint", endpoint )

        api_key = self.api_key.text()
        self.form.config.add_to_config(self.section, "api_key", api_key )

        timeout = self.timeout.text()
        self.form.config.add_to_config(self.section, "timeout", timeout )

        verify = self.verify.text()
        self.form.config.add_to_config(self.section, "verify", verify )


    def populate(self):
        config = self.form.config
        base_url = config.get(section=self.section, name="base_url", default="")
        self.base_url.setText(base_url)

        endpoint = config.get(section=self.section, name="endpoint", default="api/v1/lineage")
        self.endpoint.setText(endpoint)

        api_key = config.get(section=self.section, name="api_key", default="")
        self.api_key.setText(api_key)

        timeout = config.get(section=self.section, name="timeout", default="")
        self.timeout.setText(timeout)

        verify = config.get(section=self.section, name="verify", default="")
        self.verify.setText(verify)






