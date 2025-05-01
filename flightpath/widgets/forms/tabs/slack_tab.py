from PySide6.QtWidgets import (
    QWidget,
    QLineEdit,
    QFormLayout,
    QLabel
)


class SlackTab(QWidget):
    def __init__(self, form):
        super().__init__(form)
        self.form = form
        layout = QFormLayout()
        self.setLayout(layout)

        self.webhook_url = QLineEdit()
        layout.addRow("Webhook URL: ", self.webhook_url)

        self.webhook_url.textChanged.connect(self.form.main.on_config_changed)


    def add_to_config(self, config) -> None:
        webhook_url = self.webhook_url.text()
        self.form.config.add_to_config("slack", "webhook_url", webhook_url )

    def populate(self):
        config = self.form.config
        webhook_url = config.get(section="slack", name="webhook_url", default="")
        self.webhook_url.setText(webhook_url)




