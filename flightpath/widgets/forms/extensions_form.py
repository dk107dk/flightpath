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
        layout.addRow("CSV file extensions: ", self.csvs)

        self.csvpaths = QLineEdit()
        layout.addRow("Csvpath file extensions: ", self.csvpaths)

        self.setLayout(layout)
        self._setup()

    def add_to_config(self, config) -> None:
        config.add_to_config("extensions", "csv_files", self.csvs.text() )
        config.add_to_config("extensions", "csvpath_files", self.csvpaths.text() )

    def _setup(self) -> None:
        self.csvs.textChanged.connect(self.main.on_config_changed)
        self.csvpaths.textChanged.connect(self.main.on_config_changed)



    def populate(self):
        config = self.config
        csvs = config.csv_file_extensions
        self.csvs.setText(", ".join(csvs))
        csvpaths = config.csvpath_file_extensions
        self.csvpaths.setText(", ".join(csvpaths))



