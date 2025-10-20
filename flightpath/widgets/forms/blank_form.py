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

    @property
    def config(self) -> Config:
        return self.main.csvpath_config

    @config.setter
    def config(self, cfg:Config) -> None:
        self._config = cfg

    def add_to_config(self, config) -> None:
        ...

    def populate(self):
        ...


