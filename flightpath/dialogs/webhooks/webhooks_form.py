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
    QWidget,
)
from PySide6.QtCore import Qt, Slot


class WebhooksForm(QWidget):
    def __init__(self, *, main, parent, name: str):
        super().__init__(parent)
        self.my_parent = parent
        self.main = main
        self.name = name
        self.params_table = None
        self._setup_params_table()
        self.headers_table = None
        self._setup_headers_table()
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

        self.url = QLineEdit()
        layout.addRow("URL: ", self.url)

        #
        # =====================
        #
        overall.addWidget(form, 0)
        overall.addStretch(1)
        overall.addWidget(self.params_table, 0)
        overall.setAlignment(self.params_table, Qt.AlignBottom)

        params_inputs = QWidget()
        params_inputs_layout = QHBoxLayout()
        params_inputs_layout.setContentsMargins(0, 0, 0, 0)

        self.param_add_button = QPushButton()
        self.param_add_button.setText("Add param")
        self.param_add_button.clicked.connect(self.add_param)
        params_inputs_layout.addWidget(self.param_add_button)

        self.param_name = QLineEdit()
        params_inputs_layout.addWidget(self.param_name)
        self.param_value = QLineEdit()
        params_inputs_layout.addWidget(self.param_value)
        params_inputs.setLayout(params_inputs_layout)
        overall.addWidget(params_inputs)

        overall.addWidget(self.headers_table, 0)
        overall.setAlignment(self.headers_table, Qt.AlignBottom)

        headers_inputs = QWidget()
        headers_inputs_layout = QHBoxLayout()
        headers_inputs_layout.setContentsMargins(0, 0, 0, 0)

        self.header_add_button = QPushButton()
        self.header_add_button.setText("Add header")
        self.header_add_button.clicked.connect(self.add_header)
        headers_inputs_layout.addWidget(self.header_add_button)

        self.header_name = QLineEdit()
        headers_inputs_layout.addWidget(self.header_name)
        self.header_value = QLineEdit()
        headers_inputs_layout.addWidget(self.header_value)
        headers_inputs.setLayout(headers_inputs_layout)
        overall.addWidget(headers_inputs)

        self.setLayout(overall)

    # ===================================

    def _setup_params_table(self):
        self.params_table = QTableWidget()
        self.params_table.setContentsMargins(0, 0, 0, 0)
        self.params_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.params_table.setMinimumHeight(
            self.params_table.verticalHeader().length()
            + self.params_table.horizontalHeader().height()
            + self.params_table.frameWidth() * 2
            + 4
        )
        self.params_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.params_table.setObjectName("params_table")
        self.params_table.setColumnCount(2)
        self.params_table.setHorizontalHeaderLabels(["Param Name", "Value"])
        self.params_table.verticalHeader().setVisible(False)
        #
        # Compact data rows
        self.params_table.verticalHeader().setDefaultSectionSize(24)
        self.params_table.verticalHeader().setMinimumSectionSize(16)
        #
        # Compact header row
        self.params_table.horizontalHeader().setDefaultSectionSize(24)
        self.params_table.horizontalHeader().setMinimumSectionSize(16)
        #
        # Prevent column collapse
        self.params_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeToContents
        )
        self.params_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.Stretch
        )
        self.params_table.cellClicked.connect(self.params_click)

    @Slot(int, int)
    def params_click(self, row: int, column: int) -> None:
        if row >= 0:
            n = self.params_table.item(row, 0)
            v = self.params_table.item(row, 1)
            self.param_name.setText(n.text())
            self.param_value.setText(v.text())
            self.params_table.removeRow(row)

    def add_param(self) -> None:
        self.add_value(
            self.params_table, self.param_name.text(), self.param_value.text()
        )
        self.param_name.setText("")
        self.param_value.setText("")

    # ===================================

    def _setup_headers_table(self):
        self.headers_table = QTableWidget()
        self.headers_table.setContentsMargins(0, 0, 0, 0)
        self.headers_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.headers_table.setMinimumHeight(
            self.params_table.verticalHeader().length()
            + self.params_table.horizontalHeader().height()
            + self.params_table.frameWidth() * 2
            + 4
        )
        self.headers_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.headers_table.setObjectName("params_table")
        self.headers_table.setColumnCount(2)
        self.headers_table.setHorizontalHeaderLabels(["Header Name", "Value"])
        self.headers_table.verticalHeader().setVisible(False)
        # header.setStretchLastSection(True)
        #
        # Compact data rows
        self.headers_table.verticalHeader().setDefaultSectionSize(24)
        self.headers_table.verticalHeader().setMinimumSectionSize(16)
        #
        # Compact header row
        self.headers_table.horizontalHeader().setDefaultSectionSize(24)
        self.headers_table.horizontalHeader().setMinimumSectionSize(16)
        #
        # Prevent column collapse
        self.headers_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeToContents
        )
        self.headers_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.Stretch
        )
        self.headers_table.cellClicked.connect(self.headers_click)

    def add_header(self) -> None:
        self.add_value(
            self.headers_table, self.header_name.text(), self.header_value.text()
        )
        self.header_name.setText("")
        self.header_value.setText("")

    @Slot(int, int)
    def headers_click(self, row: int, column: int) -> None:
        if row >= 0:
            n = self.headers_table.item(row, 0)
            v = self.headers_table.item(row, 1)
            self.header_name.setText(n.text())
            self.header_value.setText(v.text())
            self.headers_table.removeRow(row)

    def add_value(self, table: QTableWidget, name: str, value: str) -> None:
        if not value or not name:
            return
        name = name.strip()
        value = value.strip()
        if name == "" or value == "":
            return
        self.updating = True
        rows = table.rowCount()
        #
        # increase the total rows by 1
        #
        table.setRowCount(rows + 1)

        n = QTableWidgetItem(name)
        n.setFlags(n.flags() & ~Qt.ItemIsEditable)
        v = QTableWidgetItem(value)
        v.setFlags(v.flags() & ~Qt.ItemIsEditable)
        #
        # oddly, we use the current row count to add the new row
        #
        table.setItem(rows, 0, n)
        table.setItem(rows, 1, v)

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
