from PySide6.QtWidgets import (
    QLineEdit,
    QPushButton,
    QFormLayout,
    QHBoxLayout,
    QWidget,
)
from PySide6.QtGui import QIntValidator


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

        self.remove_button = QPushButton()
        self.remove_button.setText("Remove")
        self.remove_button.clicked.connect(self.remove_server)

        self.add_button = QPushButton()
        self.add_button.setText("Set")
        self.add_button.clicked.connect(self.set_server)

        buttons_layout.addWidget(self.remove_button)
        buttons_layout.addWidget(self.add_button)

        layout.addWidget(buttons)

    # ===================================

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
