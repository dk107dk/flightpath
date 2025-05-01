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
        self.button_cancel_changes.setText(self.tr("Revert changes"))
        self.button_cancel_changes.setEnabled(False)
        layout.addWidget(self.button_cancel_changes)
        #
        # saves and reloads essentially everything
        #
        self.button_save = QPushButton()
        self.button_save.setText(self.tr("Save and reload"))
        self.button_save.setEnabled(False)
        layout.addWidget(self.button_save)
        #
        # this button should disable as soon as any changes have been
        # made. that will force the user to hit cancel or save. once
        # they have clicked one of those two this button reenables.
        #
        self.button_close = QPushButton()
        self.button_close.setText(self.tr("Close config"))
        layout.addWidget(self.button_close)

        self.setLayout(layout)



