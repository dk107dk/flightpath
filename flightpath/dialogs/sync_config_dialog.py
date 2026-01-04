import re
import os
import io
import json
from configparser import ConfigParser
from PySide6.QtWidgets import (
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
        QMessageBox,
        QAbstractItemView
)


from PySide6.QtGui import QAction

from PySide6.QtCore import Qt, Slot

from csvpath.util.config import Config

from flightpath.widgets.help.plus_help import HelpIconPackager
from flightpath.util.help_finder import HelpFinder
from flightpath.util.log_utility import LogUtility as lout
from flightpath.util.message_utility import MessageUtility as meut
from flightpath.util.server_utility import  ServerUtility as seut

class SyncConfigDialog(QDialog):


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

        self.setFixedHeight(620)
        self.setFixedWidth(600)

        self.setWindowTitle(f"Update the {self.name} project config")
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
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.setLayout(self.layout)

        #
        # current config
        #
        self.table_of_existing = QTableWidget()
        self.table_of_existing.setFixedHeight(265)
        self.table_of_existing.setColumnCount(2)
        self.table_of_existing.setHorizontalHeaderLabels(["Name", "Local Value (Click to copy)"])
        self.table_of_existing.verticalHeader().setVisible(False)
        header = self.table_of_existing.horizontalHeader()
        header.setStretchLastSection(True)
        self.populate_existing()
        self.table_of_existing.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table_of_existing.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)

        self.table_of_existing.itemClicked.connect(self.table_of_existing_clicked)
        self.main.show_now_or_later(self.table_of_existing)
        self.layout.addWidget(self.table_of_existing)

        #
        # server config to be updated
        #
        self.table_of_sending = QTableWidget()
        self.table_of_sending.setFixedHeight(265)
        self.table_of_sending.setColumnCount(2)
        self.table_of_sending.setHorizontalHeaderLabels(["Name", "Server Value (Click to edit)"])
        self.table_of_sending.verticalHeader().setVisible(False)
        header = self.table_of_sending.horizontalHeader()
        header.setStretchLastSection(True)
        self.populate_sending()
        self.table_of_sending.itemChanged.connect(self.handle_item_changed)
        self.main.show_now_or_later(self.table_of_sending)
        self.layout.addWidget(self.table_of_sending)

        add_form_inputs = QWidget()
        add_form_inputs_layout = QVBoxLayout()
        add_form_inputs_layout.setContentsMargins(0, 0, 0, 0)
        add_form_inputs.setLayout(add_form_inputs_layout)

        self.sync_button = QPushButton("Sync")
        self.layout.addWidget(self.sync_button)
        self.sync_button.setEnabled(False)
        self.sync_button.clicked.connect(self.do_sync)



#==================
# upload event
#==================

    def populate_table(self, *, table:QTableWidget, config:ConfigParser, editable:bool=False) -> None:
        forms = self.main.config.config_panel.forms_by_section
        t = self.main.config.config_panel.total_server_fields
        table.setRowCount(t)
        row = 0
        for i, form in enumerate(forms):
            try:
                for j, field in enumerate(form.server_fields):
                    value = config[form.section][field]
                    if isinstance(value, list):
                        value = ",".join(value)
                    k = QTableWidgetItem(f"[{form.section}] {field}")
                    v = QTableWidgetItem(value)
                    k.setFlags(k.flags() & ~Qt.ItemIsEditable)
                    if not editable:
                        v.setFlags(v.flags() & ~Qt.ItemIsEditable)
                    table.setItem(row, 0, k)
                    table.setItem(row, 1, v)
                    row += 1
                for tab in form.tabs:
                    if tab is None:
                        continue
                    print(f"tasx: {tab}: {tab.server_fields}")
                    for k, field in enumerate(tab.server_fields):
                        value = config[tab.section][field]
                        print(f"tax: {tab.section}: {field}: {value}")
                        if isinstance(value, list):
                            value = ",".join(value)
                        k = QTableWidgetItem(f"[{tab.section}] {field}")
                        v = QTableWidgetItem(value)
                        k.setFlags(k.flags() & ~Qt.ItemIsEditable)
                        if not editable:
                            v.setFlags(v.flags() & ~Qt.ItemIsEditable)
                        table.setItem(row, 0, k)
                        table.setItem(row, 1, v)
                        row += 1

            except Exception as ex:
                import traceback
                print(traceback.format_exc())
                print(f"error in populate existing: {ex}")

    def populate_sending(self) -> None:
        form = self.main.config.config_panel.get_form( "ServerForm" )
        host = form.host.text()
        cfgstr = seut.download_config(host=host, project=self.name, headers=form._headers)
        c = ConfigParser()
        c.read_string(cfgstr)
        self.populate_table(table=self.table_of_sending, config=c, editable=True)


    def populate_existing(self) -> None:
        cfg = self.main.csvpath_config
        self.populate_table(table=self.table_of_existing, config=cfg.config_parser)

    def do_sync(self) -> None:
        #
        #
        #
        form = self.main.config.config_panel.get_form( "ServerForm" )
        config_str = self._table_of_sending_to_config(form)
        form._upload_config(self.name, config_str, prompt=False)
        self.accept()

    def _table_of_sending_to_config(self, form) -> str:
        #
        # get the whole current server config
        #
        cfgstr = seut.download_config(host=form.host.text(), project=self.name, headers=form._headers)
        c = ConfigParser()
        c.read_string(cfgstr)
        #
        # iterate on the table updating the config
        #
        rows = self.table_of_sending.rowCount()
        for row in range(rows):
            name = self.table_of_sending.item(row, 0)
            value = self.table_of_sending.item(row, 1)
            section = name.text()
            name = section[section.find(" ")+1:]
            section = section[0:section.find(" ")]
            section = section.strip("]")
            section = section.strip("[")
            v = value.text()
            if not c.has_section(section):
                c.add_section(section)
            c[section][name] = v
        #
        # serialize the ConfigParser to str
        #
        config_str = self._get_config_str(c)
        return config_str

    def _get_config_str(self, config:ConfigParser) -> str:
        string_buffer = io.StringIO()
        config.write(string_buffer)
        config_str = string_buffer.getvalue()
        return config_str

#==================
# lists events
#==================


    @Slot(QTableWidgetItem)
    def handle_item_changed(self, item) -> None:
        row = item.row()
        value = self.table_of_sending.item(row, 1)
        self.sync_button.setEnabled(True)

    @Slot(QTableWidgetItem)
    def table_of_existing_clicked(self, item) -> None:
        row = item.row()
        name = self.table_of_existing.item(row, 0)
        value = self.table_of_existing.item(row, 1)
        value_s = self.table_of_sending.item(row, 1)
        if value.text() != value_s.text():
            k = QTableWidgetItem(name.text())
            v = QTableWidgetItem(value.text())
            k.setFlags(k.flags() & ~Qt.ItemIsEditable)
            self.table_of_sending.setItem(row, 0, k)
            self.table_of_sending.setItem(row, 1, v)
            self.sync_button.setEnabled(True)



