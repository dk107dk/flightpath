from PySide6.QtCore import QThreadPool
from PySide6.QtWidgets import (
    QLineEdit,
    QMessageBox,
    QPushButton,
    QFormLayout,
    QHBoxLayout,
    QWidget,
)
from PySide6.QtGui import QIntValidator

from flightpath.util.message_utility import MessageUtility as meut
from flightpath.workers.sftp_test_worker import SftpTestWorker


class SftpForm(QWidget):
    def __init__(self, *, main, parent):
        super().__init__(parent)
        self.my_parent = parent
        self.main = main

        #
        # =====================
        #
        layout = QFormLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        self.name = QLineEdit()
        layout.addRow("Name", self.name)

        self.server = QLineEdit()
        layout.addRow("Server", self.server)

        self.port = QLineEdit()

        validator = QIntValidator(self)
        self.port.setValidator(validator)
        layout.addRow("Port (numeric)", self.port)

        self.username = QLineEdit()
        layout.addRow("Username", self.username)

        self.password = QLineEdit()
        layout.addRow("Password", self.password)

        buttons = QWidget()
        buttons_layout = QHBoxLayout()
        buttons.setLayout(buttons_layout)

        self.test_button = QPushButton()
        self.test_button.setText("Test Connection")
        self.test_button.clicked.connect(self.test_connection)

        self.remove_button = QPushButton()
        self.remove_button.setText("Remove")
        self.remove_button.clicked.connect(self.remove_server)

        self.add_button = QPushButton()
        self.add_button.setText("Set")
        self.add_button.clicked.connect(self.set_server)

        buttons_layout.addWidget(self.test_button)
        buttons_layout.addWidget(self.remove_button)
        buttons_layout.addWidget(self.add_button)

        layout.addRow("", buttons)

    # ===================================

    def test_connection(self) -> None:
        server = self.server.text().strip()
        if not server:
            meut.message2(
                parent=self,
                title="Missing server",
                msg="Enter a server address before testing the connection.",
            )
            return
        port_text = self.port.text().strip()
        try:
            port = int(port_text) if port_text else 22
        except ValueError:
            port = 22
        username = self.username.text().strip()
        password = self.password.text()
        self.test_button.setEnabled(False)
        self.test_button.setText("Testing…")
        worker = SftpTestWorker(
            server=server, port=port, username=username, password=password
        )
        worker.signals.finished.connect(self.on_test_result)
        QThreadPool.globalInstance().start(worker)

    def on_test_result(self, success: bool, message: str) -> None:
        self.test_button.setEnabled(True)
        self.test_button.setText("Test Connection")
        title = "Connection Successful" if success else "Connection Failed"
        icon = QMessageBox.Information if success else QMessageBox.Warning
        meut.message2(parent=self, title=title, msg=message, icon=icon)

    def set_server(self) -> None:
        print("sftp form: set_server")
        self.my_parent.update_server()

    def remove_server(self) -> None:
        name = self.name.text()
        print(f"remove_server: removing {name}")
        self.my_parent.remove_server(name)
        print("remove_server: done")

    def update_dark(self) -> None:
        """
        if hasattr(self, "msg1"):
            css = (
                "QLabel { margin-left:auto; margin-right:auto; font-style:italic;color:#bbb; }"
                if darkdetect.isDark()
                else "QLabel { margin-left:auto; margin-right:auto; font-style:italic;color:#222; }"
            )
            self.msg1.setStyleSheet(css)
            self.msg2.setStyleSheet(css)
        """
