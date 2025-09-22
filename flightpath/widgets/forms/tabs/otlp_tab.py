import os
from PySide6.QtWidgets import (
    QWidget,
    QLineEdit,
    QFormLayout,
    QLabel
)


class OtlpTab(QWidget):
    def __init__(self, form):
        super().__init__()
        self.form = form

        layout = QFormLayout()
        self.setLayout(layout)

        self.endpoint = QLineEdit()
        layout.addRow("Exporter endpoint: ", self.endpoint)

        self.headers = QLineEdit()
        layout.addRow("Exporter headers: ", self.headers)

        msg = QLabel(
"""These values live in the OS env or a FlightPath Server
 project env file. You can also manage them in the env
 tab in the vertical tab list to the left as
 OTEL_EXPORTER_OTLP_HEADERS and
 OTEL_EXPORTER_OTLP_ENDPOINT.""")
        msg.setStyleSheet("QLabel { font-size: 12pt; font-style:italic;color:#222222;}")
        layout.addRow("", msg)

        self.headers.textChanged.connect(self.form.main.on_config_changed)
        self.endpoint.textChanged.connect(self.form.main.on_config_changed)

    def add_to_config(self, config) -> None:
        #
        # we don't set values in ConfigEnv in FlightPath. FlightPath Server
        # will lookup keys for var sub in ConfigEnv, but we have to manually
        # (as in by selecting during deploy from FlightPath or by editing the
        # env.json) to server projects.
        #
        # here we're multiple project, but single user, so while the user
        # may have to reset their env vars when they hop between projects we
        # at least don't have a problem with one user's env vars leaking to
        # other users -- so we can just set the env. also for OTLP its pretty
        # likely there's just one endpoint for all projects.
        #
        headers = self.headers.text()
        os.environ["OTEL_EXPORTER_OTLP_HEADERS"] = headers

        endpoint = self.endpoint.text()
        os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"] = endpoint

    def populate(self):
        config = self.form.config
        headers = config.get(section=None, name="OTEL_EXPORTER_OTLP_HEADERS")
        if headers:
            self.headers.setText(headers)
        #
        # setting section=None passes this down to the ConfigEnv which knows
        # how to do var lookup/sub without going through config.ini
        #
        endpoint = config.get(section=None, name="OTEL_EXPORTER_OTLP_ENDPOINT")
        if endpoint:
            self.endpoint.setText(endpoint)






