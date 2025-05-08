from PySide6.QtWidgets import ( # pylint: disable=E0611
        QWidget,
        QVBoxLayout,
        QHBoxLayout,
        QPushButton,
        QLabel,
        QDialog,
        QLineEdit,
        QFormLayout,
        QComboBox,
        QScrollArea,
)
from PySide6.QtCore import Qt # pylint: disable=E0611

from csvpath import CsvPaths
#from flightpath.widgets.help.plus_help import HelpIconPackager
#from flightpath.util.help_finder import HelpFinder
from flightpath.widgets.json_tree_model.json_tree_item import TreeItem

class PickPathsDialog(QDialog):

    def __init__(self, *, main, tree, parent_item):
        super().__init__(main)
        self.main = main
        self.tree = tree
        self.parent = parent_item

        self.setWindowTitle("Pick or add a named-path")

        self.setFixedHeight(200)
        self.setFixedWidth(430)

        main_layout = QVBoxLayout()
        self.setLayout(main_layout)
        self.setWindowModality(Qt.ApplicationModal)

        clabel = QLabel()
        clabel.setText("Pick an existing named-paths group")
        clabel.setWordWrap(False)
        main_layout.addWidget(clabel)

        self.existing_group_ctl = QComboBox()
        self.existing_group_ctl.setStyleSheet("QComboBox { width:450px }")
        self.existing_group_ctl.clear()
        self.existing_group_ctl.addItem("...")
        for name in CsvPaths().paths_manager.named_paths_names:
            self.existing_group_ctl.addItem(name)
        main_layout.addWidget(self.existing_group_ctl)

        self.named_paths_name_ctl = QLineEdit()
        clabel = QLabel()
        clabel.setText("Or add a new named-paths name")
        clabel.setWordWrap(False)
        main_layout.addWidget(clabel)
        main_layout.addWidget(self.named_paths_name_ctl)

        self.add_button = QPushButton()
        self.add_button.setText("Add")
        self.add_button.clicked.connect(self._add)
        self.cancel_button = QPushButton()
        self.cancel_button.setText("Cancel")
        self.cancel_button.clicked.connect(self.reject)

        #
        # add the QWidget
        #
        buttons = QWidget()
        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(self.cancel_button)
        buttons_layout.addWidget(self.add_button)
        buttons.setLayout(buttons_layout)
        main_layout.addWidget(buttons)
        self.show_dialog()

    def _add(self):
        print(f"pick_paths_dialog: adding")
        named_paths_name = self.named_paths_name_ctl.text()
        existing = self.existing_group_ctl.currentText()
        if named_paths_name and named_paths_name.strip() == "" and existing == "...":
            print(f"pick_paths_dialog: not adding")
            self.close()
            return

        named_paths_name = named_paths_name if (named_paths_name and named_paths_name.strip() != "") else existing
        print(f"pick_paths_dialog: adding name: {named_paths_name}")
        self.tree.beginResetModel()
        item = TreeItem(self.parent)
        item.key = named_paths_name
        item.value_type = type([])
        self.parent.appendChild(item)
        self.tree.endResetModel()
        print(f"pick_paths_dialog: added: {item}")
        self.close()

    def show_dialog(self) -> None:
        self.exec()
