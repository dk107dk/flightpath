from PySide6.QtWidgets import (  # pylint: disable=E0611
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QDialog,
    QFormLayout,
    QComboBox,
    QSizePolicy,
)
from PySide6.QtCore import Qt  # pylint: disable=E0611


from flightpath.widgets.help.plus_help import HelpIconPackager
from flightpath.util.help_finder import HelpFinder
from flightpath.util.message_utility import MessageUtility as meut


class ActivationDialog(QDialog):
    COLLECT_SERIAL = "Collect"
    FF_SERIAL = "Fast-forward"
    COLLECT_BY_LINE = "Collect by line"
    FF_BY_LINE = "Fast-forward by line"

    METHODS = {}
    METHODS[COLLECT_SERIAL] = "collect_paths"
    METHODS[FF_SERIAL] = "fast_forward_paths"
    METHODS[COLLECT_BY_LINE] = "collect_by_line"
    METHODS[FF_BY_LINE] = "fast_forward_by_line"

    METHOD_NAMES = [COLLECT_SERIAL, FF_SERIAL, COLLECT_BY_LINE, FF_BY_LINE]

    def __init__(self, *, main, named_file, parent):
        super().__init__(parent)
        self.main = main
        self.csvpaths = main.csvpaths
        self.sidebar = parent
        self.setWindowTitle(f"Run when new {named_file} data arrives")

        self.method = None
        self.named_file_name = named_file
        #
        # while we don't want to set it up yet, self.named_paths_name_ctl needs to
        # be a thing because self.named_file_name_ctl will update and the event
        # handler wants to check both members.
        #
        self.named_paths_name_ctl = None
        self.set_button = QPushButton()
        self.set_button.setText("Set")
        self.set_button.clicked.connect(self.do_set)
        self.set_button.setEnabled(False)
        self.cancel_button = QPushButton()
        self.cancel_button.setText("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        #
        #
        #
        self.setFixedHeight(110)
        self.setFixedWidth(650)

        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)

        form_layout = QFormLayout()
        form_layout.setRowWrapPolicy(QFormLayout.RowWrapPolicy.DontWrapRows)
        main_layout.addLayout(form_layout)

        #
        # named paths name
        #
        self.named_paths_name_ctl = QComboBox()
        self.named_paths_name_ctl.setEditable(True)
        self.named_paths_name_ctl.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Preferred
        )
        names = self.csvpaths.paths_manager.named_paths_names
        names.sort()
        for _ in names:
            self.named_paths_name_ctl.addItem(_)
        self.named_paths_name_ctl.editTextChanged.connect(self.on_names_change)

        box = HelpIconPackager.add_help(
            main=self.sidebar.main,
            widget=self.named_paths_name_ctl,
            on_help=self.on_help_named_paths,
        )
        form_layout.addRow("Named-paths name: ", box)
        #
        # if we have an on_arrival already stored, select it.
        #
        d = self.csvpaths.file_manager.describer
        oa = d.get_on_arrival(self.named_file_name)
        if oa is not None and not len(oa) == 0:
            n = oa["named_paths_group"]
            self.named_paths_name_ctl.setEditText(n)

        self.run_method_ctl = QComboBox()
        self.run_method_ctl.setStyleSheet("QComboBox { width:450px }")
        self.run_method_ctl.clear()
        for name in ActivationDialog.METHOD_NAMES:
            self.run_method_ctl.addItem(name)
        box = HelpIconPackager.add_help(
            main=self.sidebar.main,
            widget=self.run_method_ctl,
            on_help=self.on_help_run_method,
        )
        box.layout().addStretch()
        form_layout.setFieldGrowthPolicy(
            QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow
        )
        form_layout.addRow("Run method: ", box)
        #
        # if we have an on_arrival set the existing run method
        #
        if oa is not None and not len(oa) == 0:
            n = oa["run_method"]
            if str(n).strip() != "":
                k = next((k for k, v in self.METHODS.items() if v == n), None)
                index = self.run_method_ctl.findText(k)
                self.run_method_ctl.setCurrentIndex(index)

        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(self.cancel_button)
        buttons_layout.addWidget(self.set_button)
        self.on_names_change()
        main_layout.addLayout(buttons_layout)

    def on_help_named_paths(self) -> None:
        md = HelpFinder(main=self.sidebar.main).help("run/named_paths.md")
        if md is None:
            self.sidebar.main.helper.close_help()
            return
        self.sidebar.main.helper.get_help_tab().setMarkdown(md)
        if not self.sidebar.main.helper.is_showing_help():
            self.sidebar.main.helper.on_click_help()

    def on_help_run_method(self) -> None:
        md = HelpFinder(main=self.sidebar.main).help("run/run_method.md")
        if md is None:
            self.sidebar.main.helper.close_help()
            return
        self.sidebar.main.helper.get_help_tab().setMarkdown(md)
        if not self.sidebar.main.helper.is_showing_help():
            self.sidebar.main.helper.on_click_help()

    def on_names_change(self) -> None:
        p = self.named_paths_name_ctl.currentText()
        if p and p.strip() != "":
            self.set_button.setEnabled(True)
        else:
            self.set_button.setEnabled(False)

    def show_dialog(self) -> None:
        #
        # check if we have enough names to run
        #
        if self.csvpaths.paths_manager.total_named_paths() == 0:
            #
            #
            #
            meut.message(
                parent=self,
                title="No CsvPath statement groups",
                msg="You must load a named-paths group before you set an arrival activation",
            )
        else:
            #
            # show the dialog
            #
            self.exec()

    def do_set(self) -> None:
        npn = self.named_paths_name_ctl.currentText()
        if npn is None or str(npn).strip() == "":
            raise ValueError("Named-paths group cannot be None")
        method = self.run_method_ctl.currentText()
        if method is None or str(method).strip() == "":
            raise ValueError("Run method cannot be None")
        mgr = self.csvpaths.file_manager
        describer = mgr.describer
        j = describer.get_json(self.named_file_name)
        a = j.get(describer.ON_ARRIVAL)
        if a is None:
            a = {}
            j[describer.ON_ARRIVAL] = a
        a[describer.NAMED_PATHS_GROUP] = npn
        method = self.METHODS[method]
        a[describer.RUN_METHOD] = method
        describer.store_on_arrival(self.named_file_name, a)
        # describer.store_json(self.named_file_name, j)
        self.close()
