from PySide6.QtWidgets import (
    QWidget,
    QLineEdit,
    QFormLayout,
    QLabel
)

from csvpath.util.config import Config
from .blank_form import BlankForm

class ConfigForm(BlankForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        layout = QFormLayout()
        self.config_dir_path = QLineEdit()
        layout.addRow("Config file path: ", self.config_dir_path)
        msg = QLabel("The default is config/config.ini")
        msg.setStyleSheet("QLabel { font-size: 12pt; font-style:italic;color:#222222;}")
        layout.addRow("", msg)
        self.setLayout(layout)
        self._setup()


    def _setup(self) -> None:
        self.config_dir_path.textChanged.connect(self.main.on_config_changed)

    def add_to_config(self, config) -> None:
        path = self.config_dir_path.text()
        self.config.add_to_config("config", "path", path )



    def populate(self):
        config = self.config
        cache_path = config.get(section="config", name="path", default="config/config.ini")
        self.config_dir_path.setText(cache_path)



