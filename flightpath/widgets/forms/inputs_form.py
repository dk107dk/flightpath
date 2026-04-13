from PySide6.QtWidgets import (
    QLineEdit,
    QFormLayout,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
)
from PySide6.QtCore import Qt

from .blank_form import BlankForm


class InputsForm(BlankForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        overall = QVBoxLayout()
        self.setLayout(overall)

        form = QWidget()
        layout = QFormLayout()
        form.setLayout(layout)

        self.named_files = QLineEdit()
        layout.addRow("Named-files path or URL: ", self.named_files)

        self.named_paths = QLineEdit()
        layout.addRow("Named-paths path or URL: ", self.named_paths)
        msg = QLabel(
            "If using a non-local backend remember to update the configuration in integrations or env."
        )
        msg.setStyleSheet("QLabel { font-size: 12pt; font-style:italic;color:#222222;}")
        msg.setWordWrap(True)
        layout.addRow("", msg)

        overall.addWidget(form)
        check = QWidget()
        check_layout = QHBoxLayout()
        check.setLayout(check_layout)
        check_layout.addWidget(self.table)
        overall.addWidget(check, alignment=Qt.AlignBottom)

        self._setup()

    def _setup(self) -> None:
        self.named_paths.textChanged.connect(self.main.on_config_changed)
        self.named_files.textChanged.connect(self.main.on_config_changed)

    def add_to_config(self, config) -> None:
        config.add_to_config("inputs", "files", self.named_files.text())
        config.add_to_config("inputs", "csvpaths", self.named_paths.text())

    def populate(self):
        config = self.config
        nf = config.get(section="inputs", name="files", string_parse=False, swaps=False)
        self.named_files.setText(nf)
        np = config.get(
            section="inputs", name="csvpaths", string_parse=False, swaps=False
        )
        self.named_paths.setText(np)

        print(f"inputsfprls: np 1: {nf}")
        print(f"inputsfprls: np 2: {config.get(section='inputs', name='files')}")

        print(f"inputsfprls: np 1: {np}")
        print(f"inputsfprls: np 2: {config.get(section='inputs', name='csvpaths')}")

    @property
    def fields(self) -> list[str]:
        return ["files", "csvpaths"]

    @property
    def server_fields(self) -> list[str]:
        return self.fields

    @property
    def section(self) -> str:
        return "inputs"

    @property
    def tabs(self) -> list[str]:
        return []
