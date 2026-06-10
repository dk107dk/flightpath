from PySide6.QtWidgets import (  # pylint: disable=E0611
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QDialog,
    QWidget,
)
from PySide6.QtCore import Qt  # pylint: disable=E0611

from csvpath.managers.paths.paths_descriptor import Transfer, Transfers


from flightpath.dialogs.state_panel.state_panel import StatePanel
from flightpath.dialogs.transfers.transfers_form import TransfersForm
from flightpath.widgets.help.plus_help import HelpIconPackager
from flightpath.util.help_finder import HelpFinder


class TransfersDialog(QDialog):
    def __init__(self, *, main, name, parent):
        super().__init__(None)
        self.main = main
        self.my_parent = parent
        self.name = name

        self.setWindowTitle(f"Configure Transfers For {name}")
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        self.setWindowModality(Qt.NonModal)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(main_layout)

        self.panel = StatePanel(parent=self, main=self.main, form=TransfersForm)
        main_layout.addWidget(self.panel)

        self.method = None
        self.set_button = QPushButton()
        self.set_button.setText("Set")
        self.set_button.clicked.connect(self.do_set)
        self.set_button.setEnabled(True)
        self.cancel_button = QPushButton()
        self.cancel_button.setText("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        #
        self.setFixedHeight(250)
        self.setFixedWidth(730)

        buttons_layout = QHBoxLayout()
        buttons_layout.setContentsMargins(10, 0, 0, 10)

        buttons_layout.addWidget(self.cancel_button)
        buttons_layout.addWidget(self.set_button)

        self.buttons = QWidget()
        self.buttons.setLayout(buttons_layout)
        box = HelpIconPackager.add_help(
            main=self.main, widget=self.buttons, on_help=self.on_help_transfers
        )
        box.setStyleSheet("ClickableLabel {margin-bottom:10px;margin-right:10px;}")

        main_layout.addWidget(box)
        self._populate()

    @property
    def csvpath_ids(self) -> list[str]:
        ids = self.main.csvpaths.paths_manager.get_identified_path_names_in(self.name)
        lst = []
        for i, _ in enumerate(ids):
            if str(_).strip() in ["", "None"]:
                _ = str(i)
            lst.append(_)
        return lst

    def do_set(self) -> None:
        mgr = self.main.csvpaths.paths_manager
        group_transfers = mgr.describer.get_transfers(self.name)
        if group_transfers is None:
            raise ValueError("Transfers config cannot be None")

        ids = self.csvpath_ids
        for i, _ in enumerate(ids):
            transfers = None
            if _ in group_transfers.path_transfers:
                transfers = group_transfers.path_transfers[_]
            else:
                transfers = Transfers()
                group_transfers.path_transfers[_] = transfers
            transfers.on_complete_all = self._get_all_tranfers(_)
            transfers.on_complete_error = self._get_error_tranfers(_)
            transfers.on_complete_valid = self._get_valid_tranfers(_)
            transfers.on_complete_invalid = self._get_invalid_tranfers(_)

        mgr.describer.store_transfers(self.name, group_transfers)
        self.close()

    def _get_all_tranfers(self, csvpath: str) -> list[Transfer]:
        return self._get_transfers_by_form(form_name="all", csvpath_name=csvpath)

    def _get_error_tranfers(self, csvpath: str) -> list[Transfer]:
        return self._get_transfers_by_form(form_name="error", csvpath_name=csvpath)

    def _get_valid_tranfers(self, csvpath: str) -> list[Transfer]:
        return self._get_transfers_by_form(form_name="valid", csvpath_name=csvpath)

    def _get_invalid_tranfers(self, csvpath: str) -> list[Transfer]:
        return self._get_transfers_by_form(form_name="invalid", csvpath_name=csvpath)

    def _get_transfers_by_form(
        self, *, form_name: str, csvpath_name: str
    ) -> list[Transfer]:
        ts = []
        form = self.panel.get_form(form_name)
        table = form.transfers_table
        rows = table.rowCount()
        for row in range(0, rows):
            csvpath = table.item(row, 0)
            if csvpath.text() == csvpath_name:
                ffrom = table.item(row, 1)
                to = table.item(row, 2)
                t = Transfer()
                t.file = ffrom.text()
                t.transfer_to = to.text()
                ts.append(t)
        return ts

    def _populate(self) -> None:
        mgr = self.main.csvpaths.paths_manager
        group = mgr.describer.get_transfers(self.name)
        if group is None:
            raise ValueError("Transfers config cannot be None")

        for pathsname, transfers in group.path_transfers.items():
            form = self.panel.get_form("all")
            for _ in transfers.on_complete_all:
                form.add_value(
                    csvpath_id=pathsname, result_file=_.file, dest_var=_.transfer_to
                )

            form = self.panel.get_form("valid")
            for _ in transfers.on_complete_valid:
                form.add_value(
                    csvpath_id=pathsname, result_file=_.file, dest_var=_.transfer_to
                )

            form = self.panel.get_form("invalid")
            for _ in transfers.on_complete_invalid:
                form.add_value(
                    csvpath_id=pathsname, result_file=_.file, dest_var=_.transfer_to
                )

            form = self.panel.get_form("error")
            for _ in transfers.on_complete_error:
                form.add_value(
                    csvpath_id=pathsname, result_file=_.file, dest_var=_.transfer_to
                )

    def on_help_transfers(self) -> None:
        md = HelpFinder(main=self.main).help("transfers/transfers.md")
        if md is None:
            self.main.helper.close_help()
            return
        self.main.helper.get_help_tab().setMarkdown(md)
        if not self.main.helper.is_showing_help():
            self.main.helper.on_click_help()

    def show_dialog(self) -> None:
        self.show()
