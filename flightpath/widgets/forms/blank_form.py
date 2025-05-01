from PySide6.QtWidgets import (
    QWidget,
    QFormLayout,
    QVBoxLayout,
    QLabel
)
from PySide6.QtCore import Qt
from csvpath.util.config import Config

class BlankForm(QWidget):
    def __init__(self, main=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._config = None
        self.main = main

        """
        #
        # this works for this particular form. but it breaks the tree view. if
        # uncomment below tree view stops switching between forms. unsure why.
        #
        self.layout = QVBoxLayout()
        self.layout.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)
        self.label_top = QLabel()
        self.label_top.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_top.setStyleSheet("font-size: 14px;")
        self.label_top.setText(self.tr(f"Edit settings from your current config file at {main.csvpath_config.config_path}. You can change the location and contents of the file at any time."))
        self.layout.addWidget(self.label_top)
        self.setLayout(self.layout)
        """

    @property
    def config(self) -> Config:
        return self._config

    @config.setter
    def config(self, cfg:Config) -> None:
        self._config = cfg

    def add_to_config(self, config) -> None:
        ...

    def populate(self):
        ...


