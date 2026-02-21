from PySide6.QtWidgets import (
        QDialog,
        QWidget,
        QVBoxLayout,
        QFormLayout,
        QComboBox,
        QLabel,
        QPushButton,
        QLineEdit,
        QDialogButtonBox
)
from PySide6.QtCore import QSize, Qt

class SaveCsvToDialog(QDialog):
    def __init__(self, *, parent=None, main, path):
        super().__init__(parent)

        self.main = main
        self.path = path
        self.setWindowTitle("Save to")
        self.setFixedSize(QSize(520, 150))

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(4)
        self.path_ctrl = QLineEdit()
        self.path_ctrl.setText(self.path)
        layout.addWidget(self.path_ctrl)


        form = QWidget()
        form_layout = QFormLayout()
        form_layout.setContentsMargins(3, 3, 3, 3)
        form_layout.setSpacing(6)
        form.setLayout(form_layout)
        layout.addWidget(form)

        self.delimiter = QComboBox()
        self.delimiter.setFixedSize(140, 27)
        self.delimiter.addItems(["Comma", "Pipe", "Semi-colon", "Tab"])

        self.quotechar = QComboBox()
        self.quotechar.setFixedSize(140, 27)
        self.quotechar.addItems(["Double quotes", "Single quotes"])

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        form_layout.addRow("Delimiter: ", self.delimiter)
        form_layout.addRow("Quotechar: ", self.quotechar)
        layout.addWidget(buttons) #, alignment=Qt.AlignLeft

        self.path_ctrl.textChanged.connect(self._show_hide)

    def _show_hide(self) -> None:
        if self.path_ctrl.text().endswith(".csv"):
            self.delimiter.setEnabled(True)
            self.quotechar.setEnabled(True)
        else:
            self.delimiter.setEnabled(False)
            self.quotechar.setEnabled(False)

    def get_path(self) -> str:
        return self.path_ctrl.text()

    def get_delimiter(self) -> str:
        return self.delimiter.currentText()

    def get_quotechar(self) -> str:
        return self.quotechar.currentText()



