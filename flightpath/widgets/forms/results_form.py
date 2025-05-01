from PySide6.QtWidgets import (
    QWidget,
    QLineEdit,
    QFormLayout,
    QComboBox
)

from csvpath.util.config import Config
from .blank_form import BlankForm

class ResultsForm(BlankForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        layout = QFormLayout()

        self.archive = QLineEdit()
        layout.addRow("Archive path or URL: ", self.archive)

        self.transfers = QLineEdit()
        layout.addRow("Transfers directory: ", self.transfers)

        self.setLayout(layout)
        self._setup()

    def add_to_config(self, config) -> None:
        config.add_to_config("results", "archive", self.archive.text() )
        config.add_to_config("results", "transfers", self.transfers.text() )

    def _setup(self) -> None:
        self.archive.textChanged.connect(self.main.on_config_changed)
        self.transfers.textChanged.connect(self.main.on_config_changed)


    def populate(self):
        config = self.config
        archive = config.get(section="results", name="archive")
        self.archive.setText(archive)
        transfers = config.get(section="results", name="transfers")
        self.transfers.setText(transfers)


