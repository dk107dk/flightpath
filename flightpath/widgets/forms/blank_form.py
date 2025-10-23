from typing import Self
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
        self.main = main


    def show_blank(self) -> Self:
        self.display = QWidget()
        self.display.setLayout(QVBoxLayout())
        msg = QLabel(f"Use the vertical tabs to the left to update project config settings. You are editing {self.main.csvpath_config.configpath}.")
        msg.setStyleSheet("QLabel { margin-left:auto; margin-right:auto; font-style:italic;color:#222222; }")
        msg.setFixedWidth(500)
        msg.setWordWrap(True)
        #self.display.layout().addWidget(msg)
        self.display.layout().addWidget(msg, alignment=Qt.AlignmentFlag.AlignCenter)
        self.setLayout(QVBoxLayout())
        self.layout().addWidget(self.display)
        return self


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


