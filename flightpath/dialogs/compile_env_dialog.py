import re
import os
import json
from PySide6.QtWidgets import ( # pylint: disable=E0611
        QVBoxLayout,
        QHBoxLayout,
        QPushButton,
        QLabel,
        QDialog,
        QLineEdit,
        QFormLayout,
        QComboBox,
        QSizePolicy,
        QMenu,
        QWidget,
        QPlainTextEdit,
        QLineEdit,
        QTableWidget,
        QTableWidgetItem,
        QMessageBox
)


from PySide6.QtGui import QAction

from PySide6.QtCore import Qt, Slot

from flightpath.widgets.help.plus_help import HelpIconPackager
from flightpath.util.help_finder import HelpFinder
from flightpath.util.log_utility import LogUtility as lout
from flightpath.util.message_utility import MessageUtility as meut

class CompileEnvDialog(QDialog):


    def __init__(self, *, name, parent):
        super().__init__(parent)
        self.parent = parent
        self.main = parent.main
        self.name = name
        self.evars = None
        self.context_menu = None
        #
        # config_str is the payload we're trying to get to the server
        # it is based on the self.table_of_sending.
        #
        self.config_str = None

        self.setFixedHeight(760)
        self.setFixedWidth(600)

        self.setWindowTitle(f"Collect env vars for the {self.name} project")
        self.upload_button = None # QPushButton()
        self.cancel_button = None #QPushButton()
        self.setWindowModality(Qt.ApplicationModal)
        self.main_content()

    def on_help_template(self) -> None:
        md = HelpFinder(main=self.sidebar.main).help("run/template.md")
        if md is None:
            self.sidebar.main.helper.close_help()
            return
        self.sidebar.main.helper.get_help_tab().setMarkdown(md)
        if not self.sidebar.main.helper.is_showing_help():
            self.sidebar.main.helper.on_click_help()


    def show_dialog(self) -> None:
        #
        # show the dialog
        #
        self.exec()


#================
# main part
#================


    def main_content(self) -> None:
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(15, 10, 15, 25)
        self.setLayout(self.layout)
        box = QWidget()
        form_layout = QFormLayout()
        form_layout.setContentsMargins(5, 5, 5, 5)
        box.setLayout(form_layout)
        self.layout.addWidget(box)

        self.filter_input = QLineEdit()
        form_layout.addRow("Filter: ", self.filter_input)
        self.env_value = QLineEdit()
        button = QPushButton("Update filter")
        form_layout.addRow("", button)
        button.clicked.connect(self._on_click_update)

        self.table_of_existing = QTableWidget()
        self.table_of_existing.setFixedHeight(265)
        self.table_of_existing.setColumnCount(2)
        self.table_of_existing.setHorizontalHeaderLabels(["Name", "Value"])
        self.table_of_existing.verticalHeader().setVisible(False)
        header = self.table_of_existing.horizontalHeader()
        header.setStretchLastSection(True)
        self.table_of_existing.itemClicked.connect(self.table_of_existing_clicked)
        self.main.show_now_or_later(self.table_of_existing)
        self.layout.addWidget(self.table_of_existing)

        self.table_of_sending = QTableWidget()
        self.table_of_sending.setFixedHeight(265)
        self.table_of_sending.setColumnCount(2)
        self.table_of_sending.setHorizontalHeaderLabels(["Name", "Value"])
        self.table_of_sending.verticalHeader().setVisible(False)
        header = self.table_of_sending.horizontalHeader()
        header.setStretchLastSection(True)
        self.table_of_sending.itemClicked.connect(self.table_of_sending_clicked)
        self.main.show_now_or_later(self.table_of_sending)
        self.layout.addWidget(self.table_of_sending)

        add = QWidget()
        add_form_layout = QFormLayout()
        add_form_layout.setContentsMargins(5, 5, 5, 5)
        add.setLayout(add_form_layout)
        self.layout.addWidget(add)

        add_form_inputs = QWidget()
        add_form_inputs_layout = QVBoxLayout()
        add_form_inputs_layout.setContentsMargins(0, 0, 0, 0)

        add_form_inputs.setLayout(add_form_inputs_layout)

        kv_box = QWidget()
        kv_box_layout = QHBoxLayout()
        kv_box_layout.setContentsMargins(0, 0, 0, 0)
        kv_box.setLayout(kv_box_layout)

        self.add_name = QLineEdit()
        kv_box_layout.addWidget(self.add_name)
        self.add_value = QLineEdit()
        kv_box_layout.addWidget(self.add_value)
        button = QPushButton("Add env var")

        add_form_inputs_layout.addWidget(kv_box)
        add_form_inputs_layout.addWidget(button)
        button.clicked.connect(self._on_click_add)

        add_form_layout.addRow("Add new: ", add_form_inputs)

        self.cancel_button = QPushButton("Cancel")
        self.upload_button = QPushButton("Upload")
        upload_box = QWidget()
        ubox_layout = QHBoxLayout()
        ubox_layout.setContentsMargins(0, 0, 0, 0)
        upload_box.setLayout(ubox_layout)
        ubox_layout.addWidget(self.cancel_button)
        ubox_layout.addWidget(self.upload_button)
        add_form_layout.addRow("Upload: ", upload_box)
        self.upload_button.clicked.connect(self.do_upload)
        self.cancel_button.clicked.connect(self.reject)

        self.refreshing = False
        self.refresh_table()


#==================
# upload event
#==================

    def do_upload(self) -> None:
        # this method doesn't actually send. it just compiles the env string
        # and closes so that the main env_form can send.
        payload = {"name": self.name }
        rows = self.table_of_sending.rowCount()
        _ = {}
        for row in range(rows):
            n = self.table_of_sending.item(row, 0)
            v = self.table_of_sending.item(row, 1)
            _[n.text()] = v.text()
        s = json.dumps(_)
        self.config_str = s
        self.accept()

#==================
# lists events
#==================

    @Slot(QTableWidgetItem)
    def table_of_sending_clicked(self, item) -> None:
        row = item.row()
        self.table_of_sending.removeRow(row)

    @Slot(QTableWidgetItem)
    def table_of_existing_clicked(self, item) -> None:
        row = item.row()
        name = self.table_of_existing.item(row, 0)
        value = self.table_of_existing.item(row, 1)
        i = self.table_of_sending.rowCount()
        self.table_of_sending.insertRow(i)
        k = QTableWidgetItem(name.text())
        v = QTableWidgetItem(value.text())
        self.table_of_sending.setItem(i, 0, k)
        self.table_of_sending.setItem(i, 1, v)

#==================
# filter buttons
#==================

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
        self.table_of_existing.setRowCount(len(rows))
        for k, v in rows.items():
            ki = QTableWidgetItem(k)
            vi = QTableWidgetItem(v)
            self.table_of_existing.setItem(row, 0, ki)
            self.table_of_existing.setItem(row, 1, vi)
            row += 1
        self.refreshing = False

    def _on_click_update(self) -> None:
        self.refresh_table()

    def _on_click_add(self) -> None:
        i = self.table_of_sending.rowCount()
        self.table_of_sending.insertRow(i)
        k = QTableWidgetItem(self.add_name.text())
        v = QTableWidgetItem(self.add_value.text())
        self.table_of_sending.setItem(i, 0, k)
        self.table_of_sending.setItem(i, 1, v)





