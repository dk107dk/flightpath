from PySide6.QtWidgets import (
    QWidget,
    QLineEdit,
    QFormLayout,
    QLabel
)

class SqliteTab(QWidget):
    def __init__(self, form):
        super().__init__(form)
        self.form = form
        layout = QFormLayout()
        self.setLayout(layout)

        self.db = QLineEdit()
        layout.addRow("Database file: ", self.db)

        self.db.textChanged.connect(self.form.main.on_config_changed)

    @property
    def section(self) -> str:
        return "sqlite"

    @property
    def server_fields(self) -> list[str]:
        return ["db"]

    @property
    def server_fields_count(self) -> int:
        return len(self.server_fields)


    def add_to_config(self, config) -> None:
        db = self.db.text()
        self.form.config.add_to_config(self.section, "db", db )

    def populate(self):
        config = self.form.config
        db = config.get(section=self.section, name="db", default="")
        self.db.setText(db)


