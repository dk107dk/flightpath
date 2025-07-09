from PySide6.QtWidgets import ( # pylint: disable=E0611
        QWidget,
        QVBoxLayout,
        QHBoxLayout,
        QPushButton,
        QLabel,
        QDialog,
        QLineEdit,
        QFormLayout,
        QScrollArea,
        QCheckBox,
        QSizePolicy
)
from PySide6.QtCore import Qt, Slot #pylint: disable=E0611

from csvpath.util.nos import Nos
from csvpath.util.path_util import PathUtility as pathu

from flightpath.widgets.clickable_label import ClickableLabel
from flightpath.widgets.help.plus_help import HelpIconPackager
from flightpath.util.help_finder import HelpFinder
from flightpath.util.message_utility import MessageUtility as meut


class StageDataDialog(QDialog): # pylint: disable=R0902
    """ loads source data files as named-files. the resulting
        named-file is visiable in the top right-hand window """

    SET_TO_FILES_NAME = "  ... Set file's name ..."

    def __init__(self, *, path, parent):
        super().__init__(parent)
        self.sidebar = parent

        self.setWindowTitle("Stage source data files")

        self.path = path
        self.errors = None
        self.template = None
        self.named_path_name = None
        self.recurse = True
        self.area = None
        self.t_gen_area = None

        self.setFixedHeight(250)
        self.setFixedWidth(650)

        main_layout = QVBoxLayout()
        self.setLayout(main_layout)
        self.setWindowModality(Qt.ApplicationModal)

        form_layout = QFormLayout()
        main_layout.addLayout(form_layout)

        file = Nos(self.path).isfile()

        self.named_file_name_ctl = QLineEdit()

        box = HelpIconPackager.add_help(
            main=self.sidebar.main,
            widget=self.named_file_name_ctl,
            on_help=self.on_help_named_file
        )
        box.setFixedHeight(30)

        form_layout.addRow("Named-file name: ", box)


        self.separate_ctl = QCheckBox("Yes")
        self.separate_ctl.setChecked(True)
        self._set_separate_names()
        self.separate_ctl.stateChanged.connect(self._set_separate_names)

        self.recurse_ctl = QCheckBox("Yes")
        self.recurse_ctl.setChecked(self.recurse is True)
        if not file:
            form_layout.addRow("Separate named-files: ", self.separate_ctl)
            form_layout.addRow("Add files recursively: ", self.recurse_ctl)

        self._setup_area()
        if file:
            form_layout.addRow("File to register: ", self.area)
        else:
            form_layout.addRow("Register files within: ", self.area)

        # foods/:1/data/:0/:filename
        self.template_ctl = QLineEdit()
        self.template_ctl.textChanged.connect(self._update_actual_path)

        #
        # add a help icon for templates
        #
        box = HelpIconPackager.add_help(main=self.sidebar.main, widget=self.template_ctl, on_help=self.on_help_template)
        box.setFixedHeight(30)
        form_layout.addRow("Template:", box)

        self._setup_t_gen_area()
        form_layout.addRow("Path will be: ", self.t_gen_area)

        self.stage_button = QPushButton()
        self.cancel_button = QPushButton()
        self.stage_button.setText(self.tr("Stage"))
        self.cancel_button.setText(self.tr("Cancel"))

        self.stage_button.clicked.connect(self.sidebar.do_stage)
        self.cancel_button.clicked.connect(self.reject)

        buttons = QWidget()
        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(self.cancel_button)
        buttons_layout.addWidget(self.stage_button)

        buttons.setLayout(buttons_layout)
        main_layout.addWidget(buttons)

    def _set_separate_names(self) -> None:
        nos = Nos(self.path)
        if nos.isfile():
            return
        if self.separate_ctl.isChecked():
            self.named_file_name_ctl.setEnabled(False)
            self.named_file_name_ctl.setStyleSheet(""" QLineEdit {
                                                        color:#666;
                                                        background-color:#eaeaea;
                                                        font-style:italic}""")
            self.named_file_name_ctl.setText(self.SET_TO_FILES_NAME)
        else:
            self.named_file_name_ctl.setEnabled(True)
            self.named_file_name_ctl.setStyleSheet(""" QLineEdit {
                                                        color:#000;
                                                        background-color:#fff;
                                                        font-style:plain}""")
            self.named_file_name_ctl.setText("")


    def on_help_named_file(self) -> None:
        md = HelpFinder(main=self.sidebar.main).help("stage_data/named_file.md")
        if md is None:
            self.sidebar.main.helper.close_help()
            return
        self.sidebar.main.helper.get_help_tab().setMarkdown(md)
        if not self.sidebar.main.helper.is_showing_help():
            self.sidebar.main.helper.on_click_help()

    def on_help_template(self) -> None:
        md = HelpFinder(main=self.sidebar.main).help("stage_data/template.md")
        if md is None:
            self.sidebar.main.helper.close_help()
            return
        self.sidebar.main.helper.get_help_tab().setMarkdown(md)
        if not self.sidebar.main.helper.is_showing_help():
            self.sidebar.main.helper.on_click_help()

    def _setup_t_gen_area(self) -> None:
        self.t_gen_area = QScrollArea()
        self.t_gen_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.t_gen_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.t_gen_area.setWidgetResizable(False)
        self.t_gen_area.setFixedWidth(487)
        self.t_gen_area.setFixedHeight(27)
        self.t_gen_area.setStyleSheet("QScrollArea {padding:3px 0 0 0;}")
        self.t_gen_area.horizontalScrollBar().setStyleSheet("QScrollBar {height: 0px;}")
        self.t_lab = QLabel()
        self.t_lab.setText("")
        self.t_gen_area.setWidget(self.t_lab)

    def _setup_area(self) -> None:
        self.area = QScrollArea()
        self.area.setFixedWidth(487)
        self.area.setFixedHeight(27)
        self.area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # Create a content widget that can overflow
        content_widget = QWidget()
        content_widget.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.setSizeConstraint(layout.SizeConstraint.SetFixedSize)
        content_widget.setLayout(layout)
        parts = pathu.parts(self.path)
        for i, part in enumerate(parts):
            p = ClickableLabel()
            p.setText(part)
            p.clicked.connect(self._source_path_click)
            p.setStyleSheet("QLabel {color:#885522;}")
            p.adjustSize()
            layout.addWidget(p)
            if i < len(parts)-1:
                s = QLabel()
                s.setText("/")
                s.adjustSize()
                layout.addWidget(s)

        self.area.setWidget(content_widget)


    @Slot(str)
    def _source_path_click(self, text:str) -> None:
        if self.template_ctl.text().endswith(":filename"):
            meut.message(msg="Filename must be the last component of the path", title="Complete")
            return
        cursor_pos = self.template_ctl.cursorPosition()
        parts = pathu.parts(self.path)
        parts.remove("")
        i = 0
        print(f"stage_data_dialog: _source_path_click: parts: {parts}")
        try:
            i = parts.index(text)
        except ValueError:
            return
        t = self.template_ctl.text()
        top = t[0:cursor_pos]
        middle = ""
        bottom = t[cursor_pos:]
        if i == len(parts) -1:
            if top != "" and not top.endswith("/"):
                middle = "/"
            middle = f"{middle}:filename"
        else:
            bottom = f":{i}/"
            if not top.endswith("/"):
                bottom = f"/{bottom}"
        nt = f"{top}{middle}{bottom}"
        nt = nt.lstrip("/")
        self.template_ctl.setText( nt )
        #
        # update the t_lab with what the path will be
        #
        self._update_actual_path(nt)

    def _update_actual_path(self, gen_path:str) -> None:
        if gen_path is None:
            gen_path = self.template_ctl.text()
        parts = pathu.parts(self.path)
        parts.remove("")
        for i, p in enumerate(parts):
            gen_path = gen_path.replace(f":{i}", p)
        gen_path = gen_path.replace(":filename", parts[len(parts)-1])
        gen_path = gen_path.lstrip("/")
        self.t_lab.setText(gen_path)
        self.t_lab.adjustSize()

    def show_dialog(self) -> None:
        self.exec()
