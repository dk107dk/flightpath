from PySide6.QtWidgets import (
    QWidget,
    QLineEdit,
    QPushButton,
    QFormLayout
)

from csvpath.matching.functions.function_factory import FunctionFactory

from .blank_form import BlankForm

class FunctionsForm(BlankForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        layout = QFormLayout()

        self.imports_dir_path = QLineEdit()
        layout.addRow("Custom functions imports file: ", self.imports_dir_path)
        button = QPushButton("Reload custom functions")
        button.clicked.connect(self.on_click_reset)
        layout.addRow("", button)

        self.setLayout(layout)
        self._setup()

    def on_click_reset(self) -> None:
        path = self.imports_dir_path.text()
        if path is None or str(path).strip() == "":
            return
        FunctionFactory.clear_to_reload(path)
        print("cleared custom functions for {path}")

    def _setup(self) -> None:
        self.imports_dir_path.textChanged.connect(self.main.on_config_changed)

    def add_to_config(self, config) -> None:
        path = self.imports_dir_path.text()
        config.add_to_config("functions", "imports", path )

    def populate(self):
        config = self.config
        imports_path = config.get(section="functions", name="imports", default="")
        self.imports_dir_path.setText(imports_path)


    @property
    def fields(self) -> list[str]:
        return ["imports"]

    @property
    def server_fields(self) -> list[str]:
        return []

    @property
    def section(self) -> str:
        return "functions"

    @property
    def tabs(self) -> list[str]:
        return []

