from PySide6.QtWidgets import (
    QWidget,
    QLineEdit,
    QFormLayout,
    QLabel
)

class ScriptsTab(QWidget):
    def __init__(self, form):
        super().__init__(form)
        self.form = form
        layout = QFormLayout()
        self.setLayout(layout)

        self.run_scripts = QLineEdit()
        layout.addRow("Run scripts: ", self.run_scripts)

        self.shell = QLineEdit()
        layout.addRow("Shell: ", self.shell)

        self.run_scripts.textChanged.connect(self.form.main.on_config_changed)
        self.shell.textChanged.connect(self.form.main.on_config_changed)


    def add_to_config(self, config) -> None:
        run_scripts = self.run_scripts.text()
        self.form.config.add_to_config("scripts", "run_scripts", run_scripts )

        shell = self.shell.text()
        self.form.config.add_to_config("scripts", "shell", shell )

    def populate(self):
        config = self.form.config
        run_scripts = config.get(section="scripts", name="run_scripts", default="no")
        self.run_scripts.setText(run_scripts)

        shell = config.get(section="scripts", name="shell", default="/bin/bash")
        self.shell.setText(shell)



