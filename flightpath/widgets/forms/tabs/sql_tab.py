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


    def add_to_config(self, config) -> None:
        dialect = self.dialect.text()
        self.form.config.add_to_config("sql", "dialect", dialect )

        connection_string = self.connection_string.text()
        self.form.config.add_to_config("sql", "connection_string", connection_string )

    def populate(self):
        config = self.form.config
        dialect = config.get(section="sql", name="dialect", default="sqlite")
        self.dialect.setText(dialect)

        connection_string = config.get(section="sql", name="connection_string", default="sqlite:///archive/csvpath-sqlite.db")
        self.connection_string.setText(connection_string)



