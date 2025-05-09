import sys
import os

from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QPushButton,
)
from PySide6.QtGui import QIcon
from PySide6.QtCore import QSize

class ConfigToolbar(QWidget):

    def __init__(self):
        super().__init__()
        layout = QHBoxLayout()
        #
        # reloads config without changes
        #
        self.button_cancel_changes = QPushButton()
        self.button_cancel_changes.setText("Revert changes")
        self.button_cancel_changes.setEnabled(False)
        layout.addWidget(self.button_cancel_changes)
        #
        # saves and reloads essentially everything
        #
        self._button_save = QPushButton()
        self._button_save.setText("Save and reload")
        self.enable_save()
        layout.addWidget(self._button_save)
        #
        # this button should disable as soon as any changes have been
        # made. that will force the user to hit cancel or save. once
        # they have clicked one of those two this button reenables.
        #
        self.button_close = QPushButton()
        self.button_close.setText("Close config")
        self.button_close.setEnabled(True)
        layout.addWidget(self.button_close)

        self.setLayout(layout)

    def enable_save(self) -> None:
        #
        # this special method was put here for debugging a setup problem having to do with the save button.
        # it is a debugging convenience and can be removed anytime.
        #
        self._button_save.setEnabled(True)

    def disable_save(self) -> None:
        #
        # this special method was put here for debugging a setup problem having to do with the save button.
        # it is a debugging convenience and can be removed anytime.
        #
        self._button_save.setEnabled(False)


