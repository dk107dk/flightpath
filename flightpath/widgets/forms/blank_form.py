from typing import Self
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
)
from PySide6.QtCore import Qt
from csvpath.util.config import Config


class BlankForm(QWidget):
    def __init__(self, main=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.main = main
        self.updating = False
        self.table = None
        if self.fields is not None and len(self.fields) > 0:
            self.actuals_table()

    def actuals_table(self):
        self.table = QTableWidget()
        self.setStyleSheet("QTableWidget { background-color:#f8f8f8;max-height:140px;}")
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Name", "Value"])
        self.table.verticalHeader().setVisible(False)
        header = self.table.horizontalHeader()
        header.setStretchLastSection(True)
        self._update_table()
        self.table.itemChanged.connect(self._update_table)

    def _update_table(self) -> None:
        if self.updating is True:
            return
        if self.table is None:
            return
        #
        # make sure we can add rows w/o triggering updates
        #
        self.updating = True
        #
        # clear and set the row size of the table
        #
        self.table.setRowCount(0)
        self.table.setRowCount(len(self.fields))
        for row, field in enumerate(self.fields):
            ki = QTableWidgetItem(field)
            s = self.config.get(section=self.section, name=field)
            if isinstance(s, list):
                s = ",".join(s)
            vi = QTableWidgetItem(s)
            self.table.setItem(row, 0, ki)
            self.table.setItem(row, 1, vi)
        self.updating = False

    def show_blank(self) -> Self:

        self.display = QWidget()
        self.display.setLayout(QVBoxLayout())
        msg = QLabel(
            f"Use the vertical tabs to the left to update project config settings. You are editing {self.main.csvpath_config.configpath}."
        )
        msg.setStyleSheet(
            "QLabel { margin-left:auto; margin-right:auto; font-style:italic;color:#222222; }"
        )
        msg.setFixedWidth(500)
        msg.setWordWrap(True)
        self.display.layout().addWidget(msg, alignment=Qt.AlignmentFlag.AlignBottom)

        msg = QLabel(
            "Some env var substitution changes may require reopening the config panel. See the table at the bottom of most forms to see the current actual values."
        )
        msg.setStyleSheet(
            "QLabel { margin-left:auto; margin-right:auto; font-style:italic;color:#222222; }"
        )
        msg.setFixedWidth(500)
        msg.setWordWrap(True)
        self.display.layout().addWidget(msg, alignment=Qt.AlignmentFlag.AlignTop)

        self.setLayout(QVBoxLayout())
        self.layout().addWidget(self.display)
        return self

    @property
    def config(self) -> Config:
        return self.main.csvpath_config

    @config.setter
    def config(self, cfg: Config) -> None:
        self._config = cfg

    def add_to_config(self, config) -> None: ...

    def populate(self): ...

    @property
    def server_fields_count(self) -> int:
        i = len(self.server_fields)
        return i + sum(t.server_fields_count for t in self.tabs if t is not None)

    @property
    def fields(self) -> list[str]:
        return []

    @property
    def server_fields(self) -> list[str]:
        return []

    @property
    def section(self) -> str:
        return ""

    @property
    def tabs(self) -> list[str]:
        return []

    def value(self, field: str) -> str:
        return self.config.get(section=self.section, name=field)
