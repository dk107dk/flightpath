from PySide6.QtWidgets import (
    QWidget,
    QLineEdit,
    QFormLayout,
    QComboBox
)

from csvpath.util.config import Config
from .blank_form import BlankForm

class ExtensionsForm(BlankForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        layout = QFormLayout()

        self.csvs = QLineEdit()
        layout.addRow("Data file extensions: ", self.csvs)

        self.csvpaths = QLineEdit()
        layout.addRow("Csvpath file extensions: ", self.csvpaths)

        self.setLayout(layout)
        self._setup()

    def add_to_config(self, config) -> None:
        config.add_to_config("extensions", "csv_files", self.csvs.text() )
        #
        #
        #
        paths = self.csvpaths.text()
        config.add_to_config("extensions", "csvpath_files", paths )
        #
        #
        #

    def _setup(self) -> None:
        self.csvs.textChanged.connect(self.main.on_config_changed)
        self.csvpaths.textChanged.connect(self.main.on_config_changed)

    def populate(self):
        config = self.config
        csvs = config.get(section="extensions", name="csv_files")
        self.csvs.setText(", ".join(csvs))
        csvpaths = config.get(section="extensions", name="csvpath_files")
        self.csvpaths.setText(", ".join(csvpaths))



