import httpx
import traceback
from PySide6.QtWidgets import (  # pylint: disable=E0611
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QDialog,
    QLineEdit,
    QFormLayout,
    QLabel,
)
from PySide6.QtCore import Qt  # pylint: disable=E0611
from flightpath.util.message_utility import MessageUtility as meut


class NewKeyDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)

        self.setWindowTitle("Create a New API Key")
        self.setWindowModality(Qt.ApplicationModal)

        self.setFixedHeight(150)
        self.setFixedWidth(540)

        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        self.form_layout = QFormLayout()
        main_layout.addLayout(self.form_layout)

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
        main_layout.addWidget(buttons)
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
                    meut.warning2(
                        parent=self,
                        title="Cannot create new API key",
                        msg=msg,
                        callback=self.reject,
                    )
                    return
            except Exception as ex:
                print(traceback.format_exc())
                msg = f"Error sending request ({response.status_code}): {ex}"
                print(msg)
                meut.warning2(
                    parent=self,
                    title="Cannot create new API key",
                    msg=msg,
                    callback=self.reject,
                )
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
        self.form_layout.addRow("New key: ", key_label)
        self.create_button.setEnabled(False)
        self.create_button.setText("Close")
