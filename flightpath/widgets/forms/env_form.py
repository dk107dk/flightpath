import os
import re

from PySide6.QtWidgets import (
    QWidget,
    QLineEdit,
    QFormLayout,
    QVBoxLayout,
    QPushButton,
    QMessageBox,
    QTableWidget,
    QTableWidgetItem,
    QLabel
)

from csvpath.util.config import Config
from csvpath.util.nos import Nos
from flightpath.util.os_utility import OsUtility as osut
from .blank_form import BlankForm

class EnvForm(BlankForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(4, 0, 2, 0)
        self.setLayout(self.layout)
        box = QWidget()
        form_layout = QFormLayout()
        form_layout.setContentsMargins(0, 0, 0, 0)
        box.setLayout(form_layout)
        self.layout.addWidget(box)

        self.filter_input = QLineEdit()
        form_layout.addRow("Filter: ", self.filter_input)
        self.env_value = QLineEdit()
        button = QPushButton("Update filter")
        form_layout.addRow("", button)
        button.clicked.connect(self._on_click_update)

        self.evars = None
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Name", "Value"])
        self.table.verticalHeader().setVisible(False)
        header = self.table.horizontalHeader()
        header.setStretchLastSection(True)
        self.table.itemChanged.connect(self._on_item_changed)
        self.main.show_now_or_later(self.table)
        #self.table.show()
        self.layout.addWidget(self.table)

        add = QWidget()
        add_form_layout = QFormLayout()
        add_form_layout.setContentsMargins(0, 0, 0, 0)
        add.setLayout(add_form_layout)
        self.layout.addWidget(add)

        add_form_inputs = QWidget()
        add_form_inputs_layout = QVBoxLayout()
        add_form_inputs_layout.setContentsMargins(0, 0, 0, 0)

        add_form_inputs.setLayout(add_form_inputs_layout)
        self.add_name = QLineEdit()
        add_form_inputs_layout.addWidget(self.add_name)
        self.add_value = QLineEdit()
        add_form_inputs_layout.addWidget(self.add_value)
        button = QPushButton("Add env var")
        add_form_inputs_layout.addWidget(button)
        button.clicked.connect(self._on_click_add)

        add_form_layout.addRow("Add: ", add_form_inputs)

        self.refreshing = False
        self.refresh_table()


    def refresh_table(self) -> None:
        self.refreshing = True
        if self.evars is None:
            self.evars = os.environ.items()
        ffilter = self.filter_input.text()
        ffilter = ffilter if ffilter and ffilter.strip() != "" else None
        rows = {}
        for k, v in self.evars:
            if ffilter is not None:
                r = re.compile(ffilter)
                m = r.findall(k)
                if len(m) == 0:
                    continue
            rows[k] = v
        row = 0
        self.table.setRowCount(len(rows))
        for k, v in rows.items():
            ki = QTableWidgetItem(k)
            vi = QTableWidgetItem(v)
            self.table.setItem(row, 0, ki)
            self.table.setItem(row, 1, vi)
            row += 1
        self.refreshing = False

    def _on_click_update(self) -> None:
        self.refresh_table()

    def _on_click_add(self) -> None:
        #
        # add item
        #
        name = self.add_name.text()
        value = self.add_value.text()
        if value is None or value.strip() == "":
            if name in os.environ:
                del os.environ[name]
            self.main.state.set_env(name, None)
        else:
            os.environ[name] = value
            self.main.state.set_env(name, value)
        #
        # update table
        #
        self.refresh_table()

    def _on_item_changed(self, item: QTableWidgetItem) -> None:
        if self.refreshing is True:
            return
        row = item.row()
        value = self.table.item(row, 1)
        if value is None:
            return
        new_text = item.text()
        key = self.table.item(row, 0)
        k = key.text()
        if new_text is None or new_text.strip() == "":
            if k in os.environ:
                del os.environ[k]
            self.main.state.set_env(k, None)
            return
        os.environ[k] = new_text
        self.main.state.set_env(k, new_text)

    def add_to_config(self, config) -> None:
        ...

    def populate(self):
        ...

