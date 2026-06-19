from typing import Callable
import darkdetect

from PySide6.QtWidgets import (  # pylint: disable=E0611
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QDialog,
    QLineEdit,
    QFormLayout,
    QScrollArea,
    QLabel,
)
from PySide6.QtCore import Qt  # pylint: disable=E0611
from flightpath.util.message_utility import MessageUtility as meut


class NewKeyDialog(QDialog):
    def __init__(self, *, parent, failed_callback: Callable = None):
        super().__init__(parent)
        self.my_parent = parent
        self.failed_callback = failed_callback

        self.setWindowTitle("Create a New API Key")
        self.setWindowModality(Qt.ApplicationModal)

        self.setFixedHeight(150)
        self.setFixedWidth(540)

        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)

        self.key_area = None

        self.form_layout = QFormLayout()
        self.main_layout.addLayout(self.form_layout)

        self.key_name = QLineEdit()
        self.key_owner = QLineEdit()
        self.key_owner_contact = QLineEdit()
        self.form_layout.addRow("Key name: ", self.key_name)
        self.form_layout.addRow("Key owner: ", self.key_owner)
        self.form_layout.addRow("Key owner contact: ", self.key_owner_contact)

        self.cancel_button = QPushButton()
        self.cancel_button.setText("Cancel")
        self.cancel_button.clicked.connect(self.reject)

        self.create_button = QPushButton()
        text = "Create key"
        self.create_button.setText(text)
        self.create_button.clicked.connect(self.do_key_create)

        buttons = QWidget()
        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(self.cancel_button)
        buttons_layout.addWidget(self.create_button)
        buttons.setLayout(buttons_layout)
        self.main_layout.addWidget(buttons)
        self.exec()

    def do_key_create(self) -> None:
        key = None
        #
        # send request to server
        #
        _ = [
            self.key_owner.text().strip(),
            self.key_owner_contact.text().strip(),
            self.key_name.text().strip(),
        ]
        if None in _ or "" in _:
            meut.warning2(
                parent=self,
                msg="You must provide a key name and an owner name and contact",
                title="Required fields",
            )
            return
        key = None
        result = self.my_parent.api.create_key(
            key_name=self.key_name.text(),
            owner=self.key_owner.text(),
            owner_contact=self.key_owner_contact.text(),
        )
        if result.success:
            key = result.data.get("api_key")
        else:
            msg = "" if result.error_message is None else result.error_message
            msg = f"Cannot create a key. {msg} ({result.status_code})"
            if self.failed_callback:
                self.reject()
                self.failed_callback(msg=msg, code=result.status_code)
            return

        #
        # remove form fields and display the key. this is the only chance to see
        # the key.
        #
        # TODO: probably we should let the user know that, but let's wait and see
        # the experience.
        #
        while self.form_layout.rowCount() > 0:
            self.form_layout.removeRow(0)
        key_label = QLabel()
        key_label.setText(key)
        key_label.setTextInteractionFlags(Qt.TextSelectableByMouse)

        key_label.setStyleSheet("background-color: transparent;")
        self.key_area = QScrollArea()

        if darkdetect.isDark():
            self.key_area.setStyleSheet(
                "QScrollArea { padding:1px 0 0 7px; background-color:#aaa}"
            )
        else:
            self.key_area.setStyleSheet(
                "QScrollArea { padding:1px 0 0 7px; background-color:#f7f7f7}"
            )

        self.key_area.setWidgetResizable(True)
        self.key_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.key_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.key_area.setFixedHeight(33)
        self.key_area.setWidgetResizable(True)
        self.key_area.setWidget(key_label)

        self.form_layout.addRow("New key: ", self.key_area)

        msg = QLabel("Copy this key. It will not be shown again.")
        c = "eee" if darkdetect.isDark() else "222"
        msg.setStyleSheet(
            f"font-size: 12pt; font-style:italic;color:#{c}; padding:0 0 20px 0;"
        )

        self.form_layout.addRow("", msg)

        self.cancel_button.setEnabled(True)
        self.cancel_button.setText("Close")
        self.create_button.hide()
