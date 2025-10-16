from PySide6.QtWidgets import (
    QWidget,
    QLineEdit,
    QFormLayout,
    QComboBox,
    QLabel
)

from csvpath.util.config import Config
from .blank_form import BlankForm

class InputsForm(BlankForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        layout = QFormLayout()
        self.named_files = QLineEdit()
        layout.addRow("Named-files path or URL: ", self.named_files)

        self.named_paths = QLineEdit()
        layout.addRow("Named-paths path or URL: ", self.named_paths)
        msg = QLabel("If using a non-local backend remember to update the configuration in integrations or env.")
        msg.setStyleSheet("QLabel { font-size: 12pt; font-style:italic;color:#222222;}")
        msg.setWordWrap(True)
        layout.addRow("", msg)

        self.setLayout(layout)
        self._setup()

    def _setup(self) -> None:
        self.named_paths.textChanged.connect(self.main.on_config_changed)
        self.named_files.textChanged.connect(self.main.on_config_changed)


    def add_to_config(self, config) -> None:
        config.add_to_config("inputs", "files", self.named_files.text() )
        config.add_to_config("inputs", "csvpaths", self.named_paths.text() )


    def populate(self):
        config = self.config
        nf = config.get(section="inputs", name="files")
        self.named_files.setText(nf)
        np = config.get(section="inputs", name="csvpaths")
        self.named_paths.setText(np)



