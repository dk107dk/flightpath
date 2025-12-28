from PySide6.QtWidgets import (
    QWidget,
    QLineEdit,
    QFormLayout
)

from csvpath.util.config import Config
from .blank_form import BlankForm

class FunctionsForm(BlankForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        layout = QFormLayout()

        self.imports_dir_path = QLineEdit()
        layout.addRow("Custom functions imports file: ", self.imports_dir_path)

        self.setLayout(layout)
        self._setup()

    def _setup(self) -> None:
        self.imports_dir_path.textChanged.connect(self.main.on_config_changed)

    def add_to_config(self, config) -> None:
        path = self.imports_dir_path.text()
        config.add_to_config("functions", "imports", path )

    def populate(self):
        config = self.config
        imports_path = config.get(section="functions", name="imports", default="")
        self.imports_dir_path.setText(imports_path)



