import traceback

from PySide6.QtCore import Qt, QModelIndex
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QStackedLayout,
    QTreeWidget,
    QTreeWidgetItem,
)

from flightpath.util.style_utils import StyleUtility as stut


class StatePanel(QWidget):
    TREE_STYLE = """
            QTreeWidget {
                border: 1px solid #d0d0d0;
                margin: 0px;
                padding-left: 1px;
            }
            QTreeWidget::item:hover {
              color: #FFF;
              background: black;
            }
            QTreeWidget::item:selected {
              color: #FFF;
              background: gray;
            }
            """

    def __init__(self, *, main, parent, form):
        super().__init__(parent)
        self.main = main
        self.my_parent = parent
        self.form = form

        self._sections = None
        self._configurables = None
        #
        # style stuff
        #
        self.setAttribute(Qt.WA_StyledBackground, True)
        stut.set_common_style(self)
        #
        # Sidebar menu
        self._tree = None
        #
        # set up the forms
        #
        self.forms_layout = QStackedLayout()
        self.forms = None
        #
        #
        #
        self.h_layout = QHBoxLayout()
        self.layout = QVBoxLayout()
        self.h_layout.addWidget(self.tree)
        self.h_layout.addLayout(self.forms_layout)
        self.layout.addLayout(self.h_layout)
        self.setLayout(self.layout)
        #
        #
        #
        self.setup_forms()
        self.tree

    def setup_forms(self, populate=True) -> None:
        self.forms = [
            self.form(main=self.main, parent=self, formname="all"),
            self.form(main=self.main, parent=self, formname="valid"),
            self.form(main=self.main, parent=self, formname="invalid"),
            self.form(main=self.main, parent=self, formname="error"),
        ]
        for form in self.forms:
            self.forms_layout.addWidget(form)
            form.config = self.main.csvpath_config
        self.forms_layout.setCurrentIndex(0)
        self.ready = True

    def get_form(self, name: str):
        for _ in self.forms:
            if _.name == name:
                return _
        raise ValueError(f"Unknown form: {name}")

    def switch_form(self, index: QModelIndex):
        form = index.data()
        if form == "all":
            self.forms_layout.setCurrentIndex(0)
        if form == "valid":
            self.forms_layout.setCurrentIndex(1)
        if form == "invalid":
            self.forms_layout.setCurrentIndex(2)
        if form == "error":
            self.forms_layout.setCurrentIndex(3)

    @property
    def tree(self) -> QTreeWidget:
        if self._tree is None:
            tree = QTreeWidget()
            tree.setColumnCount(1)
            tree.setHeaderHidden(True)
            tree.setFixedWidth(180)
            tree.setIndentation(8)
            item = QTreeWidgetItem(tree)
            item.setText(0, "all")
            tree.setCurrentItem(item)
            item = QTreeWidgetItem(tree)
            item.setText(0, "valid")
            item = QTreeWidgetItem(tree)
            item.setText(0, "invalid")
            item = QTreeWidgetItem(tree)
            item.setText(0, "error")
            tree.clicked.connect(self.switch_form)
            tree.setStyleSheet(self.TREE_STYLE)
            self._tree = tree
        return self._tree

    def save_all_forms(self) -> None:
        for form in self.forms:
            try:
                ...
            except Exception:
                print(traceback.format_exc())
