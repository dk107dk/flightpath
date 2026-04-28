from PySide6.QtWidgets import (
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QDialog,
    QWidget,
    QFormLayout,
)
from PySide6.QtCore import Qt

from flightpath.widgets.panels.json_viewer import JsonViewer


class RunFailedDialog(QDialog):
    #
    # this dialog is specifically for when a run can't start or fails before
    # outputing anything useful. in the more usual case a run's errors can be
    # seen in its errors.json and the log. however, there are times when the
    # csvpaths mechanism gacks due to bad inputs, missing resources, etc.
    #

    def __init__(self, *, main, parent, item, cid):
        super().__init__(parent)
        self.sidebar = parent
        self.main = main
        self.item = item
        self.cid = cid
        self.setWindowTitle(f"Run Failed: {item.title.text()}")

        self.setWindowModality(Qt.ApplicationModal)
        self._error_message = QLabel(item.metadata["error_message"])
        #
        #
        #
        self.setFixedHeight(350)
        self.setFixedWidth(580)

        layout = QVBoxLayout()
        self.setLayout(layout)

        form = QWidget()
        form_layout = QFormLayout()
        form_layout.setRowWrapPolicy(QFormLayout.RowWrapPolicy.DontWrapRows)
        form.setLayout(form_layout)
        layout.addWidget(form)
        form_layout.addRow("Error message", self._error_message)

        self._view = JsonViewer.temp_file_viewer(
            main=main, parent=parent, js=item.metadata["error_json"]
        )
        layout.addWidget(self._view)

        buttons = QWidget()
        buttons_layout = QHBoxLayout()
        self.close_button = QPushButton()
        self.close_button.setText("Close")
        self.close_button.clicked.connect(self.reject)
        buttons_layout.addWidget(self.close_button)
        buttons.setLayout(buttons_layout)
        layout.addWidget(buttons)

    def show_dialog(self) -> None:
        #
        # show the dialog
        #
        self.show()

    @property
    def csvpaths(self):
        return self.item.metadata.get("csvpaths")
