import httpx
from PySide6.QtWidgets import ( # pylint: disable=E0611
        QWidget,
        QVBoxLayout,
        QHBoxLayout,
        QPushButton,
        QLabel,
        QDialog,
        QLineEdit,
        QFormLayout,
        QScrollArea,
)
from PySide6.QtCore import Qt, QFileInfo # pylint: disable=E0611

from csvpath import CsvPaths
from csvpath.util.nos import Nos

from flightpath.widgets.help.plus_help import HelpIconPackager
from flightpath.util.help_finder import HelpFinder
from flightpath.util.message_utility import MessageUtility as meut

class NewKeyDialog(QDialog):

    def __init__(self, parent):
        super().__init__(None)
        self.parent = parent

        self.setWindowTitle("Create a new API key")
        self.setWindowModality(Qt.ApplicationModal)

        self.setFixedHeight(150)
        self.setFixedWidth(540)

        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        form_layout = QFormLayout()
        main_layout.addLayout(form_layout)

        self.key_name = QLineEdit()
        self.key_owner = QLineEdit()
        self.key_owner_contact = QLineEdit()
        form_layout.addRow("Key name: ", self.key_name)
        form_layout.addRow("Key owner: ", self.key_owner)
        form_layout.addRow("Key owner contact: ", self.key_owner_contact)

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
        _ = [self.key_owner.text().strip(), self.key_owner_contact.text().strip(), self.key_name.text().strip()]
        if None in _ or "" in _:
            meut.warning(parent=self, msg="You must provide a key name and an owner name and contact", title="Required fields")
            return

        key_data = {
            "key_name": self.key_name.text(),
            "key_owner_name": self.key_owner.text(),
            "key_owner_contact": self.key_owner_contact.text()
        }
        with httpx.Client() as client:
            msg = None
            response = None
            url = f"{self.parent.host.text()}/admin/new_key"
            #
            # create a server-safeish config str here. this isn't a full cleaning. the
            # server needs to also work on the paths and check the sensitive settings
            # but we don't want to send something we know is completely unconsidered to
            # the server environment.
            #
            key = None
            try:
                response = client.post(url, json=key_data, headers=self.parent._headers)
                print(f"response: {response}")
                if response.status_code == 200:
                    key = response.json().get("api_key")
                else:
                    msg = response.json().get("detail")
                    msg = f"Cannot create a key. Server response: {response.status_code}: {msg}"
                    meut.warning(parent=self, title="Cannot create new API key", msg=msg)
                    self.reject()
                    return
            except Exception as ex:
                import traceback
                print(traceback.format_exc())
                msg = f"Error sending request ({response.status_code}): {ex}"
                print(msg)
                meut.warning(parent=self, title="Cannot create new API key", msg=msg)
                self.reject()
        #
        # use meut to show the key 1 and only 1 time
        #
        meut.input(msg="Copy this key. It will not be shown again", title="API key created", text=key)
        self.accept()

