from PySide6.QtWidgets import (
    QLineEdit,
    QFormLayout,
    QLabel,
    QVBoxLayout,
    QPushButton,
    QWidget,
    QSizePolicy,
)
from PySide6.QtCore import Qt

from csvpath.util.box import Box

from .blank_form import BlankForm


class ResultsForm(BlankForm):
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

        self.archive = QLineEdit()
        layout.addRow("Archive path or URL: ", self.archive)

        self.transfers = QLineEdit()
        layout.addRow("Transfers directory: ", self.transfers)
        msg = QLabel(
            "If using a non-local backend remember to update the configuration in integrations or env."
        )
        msg.setStyleSheet("QLabel { font-size: 12pt; font-style:italic;color:#222222;}")
        msg.setWordWrap(True)
        layout.addRow("", msg)

        button = QPushButton("Reload file trees")
        layout.addRow("", button)
        button.clicked.connect(self._on_click_reload_helpers)

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

    def _on_click_reload_helpers(self) -> None:
        self.main.question_save_config_if()
        Box().empty_my_stuff()
        self.main.load_state_and_cd()

    def add_to_config(self, config) -> None:
        config.add_to_config("results", "archive", self.archive.text())
        config.add_to_config("results", "transfers", self.transfers.text())

    def _setup(self) -> None:
        self.archive.textChanged.connect(self.main.reactor.on_config_changed)
        self.transfers.textChanged.connect(self.main.reactor.on_config_changed)

    def populate(self):
        config = self.config
        archive = config.get(
            section="results", name="archive", string_parse=False, swaps=False
        )
        self.archive.setText(archive)
        transfers = config.get(
            section="results", name="transfers", string_parse=False, swaps=False
        )
        self.transfers.setText(transfers)

    @property
    def fields(self) -> list[str]:
        return ["archive", "transfers"]

    @property
    def server_fields(self) -> list[str]:
        return self.fields

    @property
    def section(self) -> str:
        return "results"

    @property
    def tabs(self) -> list[str]:
        return []
