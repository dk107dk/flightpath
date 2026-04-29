from typing import Self
import darkdetect

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QAbstractItemView,
)
from PySide6.QtCore import Qt
from csvpath.util.config import Config


class BlankForm(QWidget):
    def __init__(self, main=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.main = main
        self.updating = False
        self.table = None
        self.is_populating = False
        if self.fields is not None and len(self.fields) > 0:
            self.actuals_table()

    def actuals_table(self):
        self.table = QTableWidget()
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setObjectName("actuals_table")
        # self.setStyleSheet("QTableWidget { background-color:#f8f8f8;max-height:140px;}")
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Name", "Actual Value"])
        self.table.verticalHeader().setVisible(False)
        header = self.table.horizontalHeader()
        header.setStretchLastSection(True)

        # Compact data rows
        self.table.verticalHeader().setDefaultSectionSize(24)
        self.table.verticalHeader().setMinimumSectionSize(16)

        # Compact header row
        self.table.horizontalHeader().setDefaultSectionSize(24)
        self.table.horizontalHeader().setMinimumSectionSize(16)

        # Prevent column collapse
        self.table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeToContents
        )
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        #
        # is this needed or helpful? we don't change the actuals table. we change
        # the fields and update the actuals behind the scenes. also update table
        # pulls from the config, not the form -- and it isn't straightforward to
        # update from the fields because we would need them to be dereferenced
        # against the env vars.
        #
        self.table.itemChanged.connect(self.update_table)

    def update_table(self) -> None:
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
        self.msg1 = QLabel(
            f"Use the vertical tabs to the left to update project config settings. You are editing {self.main.csvpath_config.configpath}."
        )
        self.msg1.setStyleSheet(
            "QLabel { margin-left:auto; margin-right:auto; font-style:italic;color:#222222; }"
        )
        self.msg1.setFixedWidth(500)
        self.msg1.setWordWrap(True)
        self.display.layout().addWidget(
            self.msg1, alignment=Qt.AlignmentFlag.AlignBottom
        )

        self.msg2 = QLabel(
            "Some env var substitution changes may require reopening the config panel. See the table at the bottom of most forms to see the current actual values."
        )
        self.msg2.setStyleSheet(
            "QLabel { margin-left:auto; margin-right:auto; font-style:italic;color:#222222; }"
        )
        self.msg2.setFixedWidth(500)
        self.msg2.setWordWrap(True)
        self.display.layout().addWidget(self.msg2, alignment=Qt.AlignmentFlag.AlignTop)
        self.update_dark()
        self.setLayout(QVBoxLayout())
        self.layout().addWidget(self.display)
        return self

    def update_dark(self) -> None:
        if hasattr(self, "msg1"):
            css = (
                "QLabel { margin-left:auto; margin-right:auto; font-style:italic;color:#bbb; }"
                if darkdetect.isDark()
                else "QLabel { margin-left:auto; margin-right:auto; font-style:italic;color:#222; }"
            )
            self.msg1.setStyleSheet(css)
            self.msg2.setStyleSheet(css)

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
