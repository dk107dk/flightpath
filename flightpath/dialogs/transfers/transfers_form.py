from PySide6.QtWidgets import (
    QLineEdit,
    QPushButton,
    QFormLayout,
    QVBoxLayout,
    QHBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QAbstractItemView,
    QSizePolicy,
    QComboBox,
    QWidget,
)
from PySide6.QtCore import Qt, Slot


class TransfersForm(QWidget):
    def __init__(self, *, main, parent, formname: str, groupname: str = None):
        super().__init__(parent)
        self.my_parent = parent
        self.main = main
        self.name = formname
        self.group = (
            groupname if groupname is not None else self.my_parent.my_parent.name
        )
        self.transfers_table = None
        self._setup_transfers_table()
        self.updating = False

        #
        # =====================
        #
        overall = QVBoxLayout()
        overall.setContentsMargins(0, 0, 0, 0)
        form = QWidget()
        layout = QFormLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        form.setLayout(layout)

        #
        # =====================
        #
        overall.addWidget(form, 0)
        overall.addStretch(1)
        overall.addWidget(self.transfers_table, 0)
        # overall.setAlignment(self.transfers_table, Qt.AlignBottom)

        params_inputs = QWidget()
        params_inputs_layout = QHBoxLayout()
        params_inputs_layout.setContentsMargins(0, 0, 0, 0)

        self.csvpath_id = QComboBox()
        self.csvpath_id.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        ids = self.my_parent.my_parent.csvpath_ids
        for _ in ids:
            self.csvpath_id.addItem(_)
        params_inputs_layout.addWidget(self.csvpath_id)

        self.result_file = QComboBox()
        self.result_file.setEditable(True)
        self.result_file.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        for _ in [
            "data",
            "unmatched",
            "vars",
            "errors",
            "printouts",
            "meta",
            "manifest",
            "source",
        ]:
            self.result_file.addItem(_)

        params_inputs_layout.addWidget(self.result_file)
        self.dest_var = QLineEdit()
        params_inputs_layout.addWidget(self.dest_var)

        self.param_add_button = QPushButton()
        self.param_add_button.setText("Add transfer")
        self.param_add_button.clicked.connect(self.add_transfer)
        params_inputs_layout.addWidget(self.param_add_button)

        params_inputs.setLayout(params_inputs_layout)
        overall.addWidget(params_inputs)

        self.setLayout(overall)

    # ===================================

    def _setup_transfers_table(self):
        self.transfers_table = QTableWidget()
        self.transfers_table.setContentsMargins(0, 0, 0, 0)
        self.transfers_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.transfers_table.setMinimumHeight(
            self.transfers_table.verticalHeader().length()
            + self.transfers_table.horizontalHeader().height()
            + self.transfers_table.frameWidth() * 2
            + 4
        )

        self.transfers_table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )
        self.transfers_table.setObjectName("transfers_table")
        self.transfers_table.setColumnCount(3)
        self.transfers_table.setHorizontalHeaderLabels(
            ["Statement ID", "File", "Variable containing destination path"]
        )
        self.transfers_table.verticalHeader().setVisible(False)
        #
        # Compact data rows
        self.transfers_table.verticalHeader().setDefaultSectionSize(24)
        self.transfers_table.verticalHeader().setMinimumSectionSize(16)
        #
        # Compact header row
        self.transfers_table.horizontalHeader().setDefaultSectionSize(24)
        self.transfers_table.horizontalHeader().setMinimumSectionSize(16)
        #
        # Prevent column collapse
        self.transfers_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeToContents
        )
        self.transfers_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeToContents
        )
        self.transfers_table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.Stretch
        )
        self.transfers_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.Interactive
        )
        self.transfers_table.horizontalHeader().setStretchLastSection(True)
        self.transfers_table.horizontalHeader().setMinimumSectionSize(125)

        self.transfers_table.cellClicked.connect(self.params_click)

    @Slot(int, int)
    def params_click(self, row: int, column: int) -> None:
        if row >= 0:
            c = self.transfers_table.item(row, 0)
            n = self.transfers_table.item(row, 1)
            v = self.transfers_table.item(row, 2)
            self.csvpath_id.setCurrentText(c.text())
            self.result_file.setCurrentText(n.text())
            self.dest_var.setText(v.text())
            self.transfers_table.removeRow(row)

    def add_transfer(self) -> None:
        self.add_value(
            csvpath_id=self.csvpath_id.currentText(),
            result_file=self.result_file.currentText(),
            dest_var=self.dest_var.text(),
        )
        self.dest_var.setText("")

    # ===================================

    def add_value(self, *, csvpath_id: str, result_file: str, dest_var: str) -> None:
        csvpath_id = str(csvpath_id).strip()
        result_file = str(result_file).strip()
        dest_var = str(dest_var).strip()
        if any([_ in ["", "None"] for _ in [csvpath_id, result_file, dest_var]]):
            return

        self.updating = True
        table = self.transfers_table
        rows = table.rowCount()
        #
        # increase the total rows by 1
        #
        table.setRowCount(rows + 1)

        cid = QTableWidgetItem(csvpath_id)
        cid.setFlags(cid.flags() & ~Qt.ItemIsEditable)
        rf = QTableWidgetItem(result_file)
        rf.setFlags(rf.flags() & ~Qt.ItemIsEditable)
        dv = QTableWidgetItem(dest_var)
        dv.setFlags(dv.flags() & ~Qt.ItemIsEditable)

        #
        # oddly, we use the current row count to add the new row
        #
        table.setItem(rows, 0, cid)
        table.setItem(rows, 1, rf)
        table.setItem(rows, 2, dv)

        self.updating = False

    #######################

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
