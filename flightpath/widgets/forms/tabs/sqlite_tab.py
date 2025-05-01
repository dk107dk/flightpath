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


    def add_to_config(self, config) -> None:
        db = self.db.text()
        self.form.config.add_to_config("sqlite", "db", db )

    def populate(self):
        config = self.form.config
        db = config.get(section="sqlite", name="db", default="")
        self.db.setText(db)


