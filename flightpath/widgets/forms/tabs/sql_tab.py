from PySide6.QtWidgets import (
    QWidget,
    QLineEdit,
    QFormLayout,
    QLabel
)

class SqlTab(QWidget):
    def __init__(self, form):
        super().__init__(form)
        self.form = form
        layout = QFormLayout()
        self.setLayout(layout)

        self.dialect = QLineEdit()
        layout.addRow("Dialect: ", self.dialect)

        self.connection_string = QLineEdit()
        layout.addRow("Connection string: ", self.connection_string)

        self.dialect.textChanged.connect(self.form.main.on_config_changed)
        self.connection_string.textChanged.connect(self.form.main.on_config_changed)

    @property
    def section(self) -> str:
        return "sql"

    @property
    def server_fields(self) -> list[str]:
        return ["dialect", "connection_string"]

    @property
    def server_fields_count(self) -> int:
        return len(self.server_fields)


    def add_to_config(self, config) -> None:
        dialect = self.dialect.text()
        self.form.config.add_to_config(self.section, "dialect", dialect )

        connection_string = self.connection_string.text()
        self.form.config.add_to_config(self.section, "connection_string", connection_string )

    def populate(self):
        config = self.form.config
        dialect = config.get(section=self.section, name="dialect", default="sqlite")
        self.dialect.setText(dialect)

        connection_string = config.get(section=self.section, name="connection_string", default="sqlite:///archive/csvpath-sqlite.db")
        self.connection_string.setText(connection_string)



