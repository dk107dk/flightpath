import httpx
import traceback
from typing import Callable

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

        key_data = {
            "key_name": self.key_name.text(),
            "key_owner_name": self.key_owner.text(),
            "key_owner_contact": self.key_owner_contact.text(),
        }
        with httpx.Client() as client:
            msg = None
            response = None
            url = f"{self.my_parent.host.text()}/admin/new_key"
            #
            # create a server-safeish config str here. this isn't a full cleaning. the
            # server needs to also work on the paths and check the sensitive settings
            # but we don't want to send something we know is completely unconsidered to
            # the server environment.
            #
            key = None
            try:
                response = client.post(
                    url, json=key_data, headers=self.my_parent._headers
                )
                if response.status_code == 200:
                    key = response.json().get("api_key")
                else:
                    msg = response.json().get("detail")
                    msg = f"Cannot create a key. Server response: {response.status_code}: {msg}"
                    if self.failed_callback:
                        self.reject()
                        self.failed_callback(msg=msg, code=response.status_code)
                    return
            except Exception as ex:
                print(traceback.format_exc())
                msg = f"Error sending request ({response.status_code}): {ex}"
                if self.failed_callback:
                    self.reject()
                    self.failed_callback(msg=msg, code=500)
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
        msg.setStyleSheet(
            "QLabel { font-size: 12pt; font-style:italic;color:#222222; padding:0 0 20px 0; }"
        )
        self.form_layout.addRow("", msg)

        self.cancel_button.setEnabled(True)
        self.cancel_button.setText("Close")
        self.create_button.hide()
