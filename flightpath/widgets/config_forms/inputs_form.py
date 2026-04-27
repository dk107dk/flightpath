from PySide6.QtWidgets import (
    QLineEdit,
    QFormLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
    QSizePolicy,
)
from PySide6.QtCore import Qt

from .blank_form import BlankForm


class InputsForm(BlankForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        #
        # =====================
        #
        overall = QVBoxLayout()
        overall.setContentsMargins(0, 0, 0, 0)
        form = QWidget()
        layout = QFormLayout()
        layout.setContentsMargins(0, 0, 0, 0)
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

        #
        # =====================
        #
        self.table.setContentsMargins(0, 0, 0, 0)
        self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.table.setMinimumHeight(
            self.table.verticalHeader().length()
            + self.table.horizontalHeader().height()
            + self.table.frameWidth() * 2
            + 4
        )
        overall.addWidget(form, 0)
        overall.addStretch(1)
        overall.addWidget(self.table, 0)
        overall.setAlignment(self.table, Qt.AlignBottom)
        self.setLayout(overall)
        self._setup()

    def _setup(self) -> None:
        self.named_paths.textChanged.connect(self.main.reactor.on_config_changed)
        self.named_files.textChanged.connect(self.main.reactor.on_config_changed)

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
