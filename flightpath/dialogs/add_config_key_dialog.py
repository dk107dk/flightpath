from PySide6.QtWidgets import ( # pylint: disable=E0611
        QWidget,
        QVBoxLayout,
        QHBoxLayout,
        QPushButton,
        QLabel,
        QDialog,
        QLineEdit,
        QFormLayout
)
from PySide6.QtCore import Qt # pylint: disable=E0611

from flightpath.widgets.json_tree_model.json_tree_item import TreeItem

class AddConfigKeyDialog(QDialog):

    def __init__(self, *, main, tree, parent_item):
        super().__init__(main)
        self.main = main
        self.tree = tree
        self.parent = parent_item

        self.setWindowTitle("Add a config key-value pair")
        self.setWindowModality(Qt.ApplicationModal)

        self.setFixedHeight(150)
        self.setFixedWidth(430)

        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        form = QWidget()
        form_layout = QFormLayout()
        form.setLayout(form_layout)
        main_layout.addWidget(form)

        clabel = QLabel()
        clabel.setText("Key")
        clabel.setWordWrap(False)
        self.key_ctl = QLineEdit()
        form_layout.addRow(clabel, self.key_ctl)

        clabel = QLabel()
        clabel.setText("Value")
        clabel.setWordWrap(False)
        self.value_ctl = QLineEdit()
        form_layout.addRow(clabel, self.value_ctl)

        self.add_button = QPushButton()
        self.add_button.setText("Add")
        self.add_button.clicked.connect(self._add)
        self.cancel_button = QPushButton()
        self.cancel_button.setText("Cancel")
        self.cancel_button.clicked.connect(self.reject)

        buttons = QWidget()
        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(self.cancel_button)
        buttons_layout.addWidget(self.add_button)
        buttons.setLayout(buttons_layout)
        main_layout.addWidget(buttons)
        self.show_dialog()

    def _add(self):
        print(f"add_config_key_dialog: adding")
        self.tree.beginResetModel()
        item = TreeItem(self.parent)
        item.key = self.key_ctl.text()
        item.value = self.value_ctl.text()
        item.value_type = type("")
        self.parent.appendChild(item)
        self.tree.endResetModel()
        self.close()

    def show_dialog(self) -> None:
        self.exec()
