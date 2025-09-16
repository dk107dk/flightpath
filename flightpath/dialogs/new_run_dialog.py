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
        QWidget,
        QPlainTextEdit,
        QMessageBox
)
from PySide6.QtCore import Qt # pylint: disable=E0611

from csvpath import CsvPaths

from flightpath.widgets.help.plus_help import HelpIconPackager
from flightpath.util.help_finder import HelpFinder
from flightpath.util.log_utility import LogUtility as lout
from flightpath.util.message_utility import MessageUtility as meut
from flightpath.workers.run_worker import RunWorker

class NewRunDialog(QDialog):
    COLLECT_SERIAL = "collect serially"
    FF_SERIAL = "fast-forward serially"
    COLLECT_BY_LINE = "collect breadth-first"
    FF_BY_LINE = "fast-forward breadth-first"

    METHODS = {}
    METHODS[COLLECT_SERIAL] = "collect_paths"
    METHODS[FF_SERIAL] = "fast_forward_paths"
    METHODS[COLLECT_BY_LINE] = "collect_by_line"
    METHODS[FF_BY_LINE] = "fast_forward_by_line"

    METHOD_NAMES = [
                COLLECT_SERIAL,
                FF_SERIAL,
                COLLECT_BY_LINE,
                FF_BY_LINE
            ]


    def __init__(self, *, named_paths=None, named_file=None, parent):
        super().__init__(parent)

        #self.csvpaths = CsvPaths()
        self.sidebar = parent
        self.setWindowTitle("Run data through a named-paths group")

        self.template = None
        self.method = None
        self.named_paths_name = named_paths
        self.named_file_name = named_file
        #
        # while we don't want to set it up yet, self.named_paths_name_ctl needs to
        # be a thing because self.named_file_name_ctl will update and the event
        # handler wants to check both members.
        #
        self.named_paths_name_ctl = None
        self.run_button = QPushButton()
        self.run_button.setText("Run")
        self.run_button.clicked.connect(self.do_run)
        self.run_button.setEnabled(False)
        self.cancel_button = QPushButton()
        self.cancel_button.setText("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        #
        #
        #
        self.setFixedHeight(200)
        self.setFixedWidth(650)

        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)

        form_layout = QFormLayout()
        form_layout.setRowWrapPolicy(QFormLayout.RowWrapPolicy.DontWrapRows)
        main_layout.addLayout(form_layout)

        self.named_file_name_ctl = QComboBox()
        self.named_file_name_ctl.setEditable(True)
        self.named_file_name_ctl.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        names = self.csvpaths.file_manager.named_file_names
        names.sort()
        for _ in names:
            self.named_file_name_ctl.addItem(_)
        self.named_file_name_ctl.editTextChanged.connect(self.on_names_change)
        box = HelpIconPackager.add_help(
            main=self.sidebar.main,
            widget=self.named_file_name_ctl,
            on_help=self.on_help_named_files
        )
        form_layout.addRow("Named-file name: ", box)
        if self.named_file_name is not None:
            self.named_file_name = self._adjust_fingerprint_if(self.named_file_name)

            self.named_file_name_ctl.setEditText(self.named_file_name)
        #
        # named paths name
        #
        self.named_paths_name_ctl = QComboBox()
        self.named_paths_name_ctl.setEditable(True)
        self.named_paths_name_ctl.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        names = self.csvpaths.paths_manager.named_paths_names
        names.sort()
        for _ in names:
            self.named_paths_name_ctl.addItem(_)
        self.named_paths_name_ctl.editTextChanged.connect(self.on_names_change)

        box = HelpIconPackager.add_help(
            main=self.sidebar.main,
            widget=self.named_paths_name_ctl,
            on_help=self.on_help_named_paths
        )
        form_layout.addRow("Named-paths name: ", box)
        if self.named_paths_name is not None:
            self.named_paths_name_ctl.setEditText(self.named_paths_name)

        self.template_ctl = QLineEdit()
        self.template_ctl.setStyleSheet("QLineEdit {height:19px;}")
        lbl = QLabel()
        lbl.setText("Template (overriding any stored with group): ")
        lbl.setWordWrap(True)
        box = HelpIconPackager.add_help(
            main=self.sidebar.main,
            widget=self.template_ctl,
            on_help=self.on_help_template
        )
        form_layout.addRow(lbl, box)
        #
        # look for template in the named-paths group
        #
        if self.named_paths_name is not None:
            template = self.csvpaths.paths_manager.get_template_for_paths(self.named_paths_name)
            if template is not None:
                self.template_ctl.setText(template)

        self.run_method_ctl = QComboBox()
        self.run_method_ctl.setStyleSheet("QComboBox { width:450px }")
        self.run_method_ctl.clear()
        for name in NewRunDialog.METHOD_NAMES:
            self.run_method_ctl.addItem(name)
        box = HelpIconPackager.add_help(
            main=self.sidebar.main,
            widget=self.run_method_ctl,
            on_help=self.on_help_run_method
        )
        box.layout().addStretch()
        form_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        form_layout.addRow("Run method: ", box)

        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(self.cancel_button)
        buttons_layout.addWidget(self.run_button)
        self.on_names_change()
        main_layout.addLayout(buttons_layout)


    def _adjust_fingerprint_if(self, name:str) -> str:
        #
        # if we end in .csv check if the user rt-clicked a fingerprint file. i.e.
        # a 64 char str + is hex number. if so, remove the .csv; otherwise, swap
        # .csv for _csv
        #
        if name.endswith(".csv"):
            _ = name[0:len(name) -4]
            rdot = _.rfind(".")
            if rdot > -1:
                fname = _[rdot+1:]
                if len(fname) == 64:
                    try:
                        int(fname, 16)
                        name = name[0:len(name) -4]
                    except ValueError:
                        name = f"{name[0:len(name)-4]}_csv"
                else:
                    name = f"{name[0:len(name)-4]}_csv"
            else:
                name = f"{name[0:len(name)-4]}_csv"
        return name

    @property
    def csvpaths(self) -> CsvPaths:
        return CsvPaths()


    def on_help_template(self) -> None:
        md = HelpFinder(main=self.sidebar.main).help("run/template.md")
        if md is None:
            self.sidebar.main.helper.close_help()
            return
        self.sidebar.main.helper.get_help_tab().setMarkdown(md)
        if not self.sidebar.main.helper.is_showing_help():
            self.sidebar.main.helper.on_click_help()

    def on_help_named_paths(self) -> None:
        md = HelpFinder(main=self.sidebar.main).help("run/named_paths.md")
        if md is None:
            self.sidebar.main.helper.close_help()
            return
        self.sidebar.main.helper.get_help_tab().setMarkdown(md)
        if not self.sidebar.main.helper.is_showing_help():
            self.sidebar.main.helper.on_click_help()

    def on_help_named_files(self) -> None:
        md = HelpFinder(main=self.sidebar.main).help("run/named_files.md")
        if md is None:
            self.sidebar.main.close_open()
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
        f = self.named_file_name_ctl.currentText()
        if self.named_paths_name_ctl:
            p = self.named_paths_name_ctl.currentText()
            if f and f.strip() != "" and p and p.strip() != "":
                self.run_button.setEnabled(True)
            else:
                self.run_button.setEnabled(False)
        else:
            self.run_button.setEnabled(False)


    def show_dialog(self) -> None:
        #
        # check if we have enough names to run
        #
        if self.csvpaths.file_manager.named_files_count == 0:
            #
            #
            #
            meut.message(title="No staged data", msg="You must stage data before you can start a run")
        if self.csvpaths.paths_manager.total_named_paths() == 0:
            #
            #
            #
            meut.message(title="No CsvPath Language files", msg="You must load csvpaths into a named-paths group before you can start a run")
        #
        # show the dialog
        #
        self.exec()

    #
    # moving here because 3 sidebars share this dialog
    #
    def do_run(self) -> None:
        template = self.template_ctl.text()
        if template and template.strip() == "":
            template = None
        self.named_file_name = self.named_file_name_ctl.currentText()
        self.named_paths_name = self.named_paths_name_ctl.currentText()
        self.method = self.run_method_ctl.currentText()

        has = False
        #
        # file manager doesn't like path separators. we could check for $ or sep.
        # could this be a problem? file manager is supposed to work with refs. :/
        #
        try:
            nfn = self.named_file_name
            if nfn.startswith("$"):
                nfn = nfn[1:nfn.find(".")]
            has = self.csvpaths.file_manager.has_named_file(nfn)
        except Exception as e:
            print(f"Error: {type(e)}: {e}")
        if not has:
            #
            # pop an error prompt
            # then leave ourselves open so they can cancel or try again
            #
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Critical)
            msg_box.setWindowTitle("Named-file name error")
            msg_box.setText(f"Unknown name: {self.named_file_name}")
            msg_box.setStandardButtons(QMessageBox.Ok)
            msg_box.exec()
            return
        try:
            npn = self.named_paths_name
            if npn.startswith("$"):
                npn = npn[1:npn.find(".")]
            has = self.csvpaths.paths_manager.has_named_paths(npn)
        except Exception as e:
            print(f"Error: {type(e)}: {e}")
        if not has:
            #
            # pop an error prompt
            # then leave ourselves open so they can cancel or try again
            #
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Critical)
            msg_box.setWindowTitle("Named-paths name error")
            msg_box.setText(f"Unknown name: {self.named_paths_name}")
            msg_box.setStandardButtons(QMessageBox.Ok)
            msg_box.exec()
            return
        #
        # we may need to shut the paths CsvPath down to release the logger. not sure yet.
        #
        self._do_run(template=template)


    def _do_run(self, template:str) -> None:
        self.sidebar.main.run_paths(
            method = NewRunDialog.METHODS.get(self.method),
            named_paths_name = self.named_paths_name ,
            named_file_name = self.named_file_name,
            template = self.template
        )
        self.close()
        return

