import os

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap, QPainter
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QSizePolicy,
    QSpacerItem,
    QMessageBox
)

from csvpath.util.file_readers import DataFileReader
from csvpath.util.file_writers import DataFileWriter
from csvpath.util.nos import Nos

from flightpath.dialogs.find_file_by_reference_dialog import FindFileByReferenceDialog
from flightpath.widgets.clickable_label import ClickableLabel
from flightpath.widgets.help.plus_help import HelpIconPackager
from flightpath.dialogs.new_run_dialog import NewRunDialog
from flightpath.util.help_finder import HelpFinder
from flightpath.util.file_utility import FileUtility as fiut
from flightpath.util.tabs_utility import TabsUtility as taut
from flightpath.util.file_collector import FileCollector

class Welcome(QWidget):

    def __init__(self, main):
        super().__init__()
        self.main = main
        self.button_copy_in = None
        main_layout = QVBoxLayout()
        main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        image_label = QLabel(self)
        imgpath = fiut.make_app_path(f"assets{os.sep}images{os.sep}flightpath-gray.svg", main=main)
        self.main.log(f"Welcome: central image path: {imgpath}")
        pixmap = QPixmap(imgpath)
        image_label.setPixmap(pixmap)
        image_label.setAlignment(Qt.AlignCenter)

        #
        # these boxes have a button + help icon
        #
        self.copy_in_box = self._copy_in_button(on_click=self.on_click_copy_in, on_help=self.on_click_copy_in_help)
        self.run_box = self._run_button(on_click=self.on_click_run, on_help=self.on_click_run_help)
        self.find_data_box = self._find_data_button(on_click=self.on_click_find_data, on_help=self.on_click_find_data_help)
        #self.validate_box = self._validate_button(on_click=self.on_click_validate, on_help=self.on_click_validate_help)

        top_layout = QVBoxLayout()
        top_layout.addWidget(image_label)
        top_layout.addWidget(self.copy_in_box)
        top_layout.addWidget(self.run_box)
        top_layout.addWidget(self.find_data_box)
        #top_layout.addWidget(self.validate_box)
        top_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        top_box = QWidget()
        top_box.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
        top_box.setLayout(top_layout)
        top_box.setFixedWidth(top_box.sizeHint().width())

        top_container = QWidget()
        top_container_layout = QHBoxLayout(top_container)
        top_container_layout.addStretch()
        top_container_layout.addWidget(top_box)
        top_container_layout.addStretch()
        top_container_layout.setContentsMargins(0, 0, 0, 0)

        top_spacer = QSpacerItem(0, 200, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        main_layout.addItem(top_spacer)
        main_layout.addWidget(top_container)
        main_layout.addStretch(1)

        self.setLayout(main_layout)
        #
        # this holds the path of a run-one-time run till the file is loaded
        # it is imaginable that we could strand the path due to some error, but
        # hard to see how the wrong path could be there when we look for a path.
        #
        self._run_one_time = None

    def on_click_copy_in(self) -> None:
        csvps = FileCollector.csvpaths_filter(self.main.csvpath_config)
        csvs = FileCollector.csvs_filter(self.main.csvpath_config)
        afilter = f"{csvps};;{csvs}"
        #
        # find dir to copy into
        #
        cwd = self.main.state.cwd
        cpath = self.main.sidebar.current_path
        cpath = cpath if cpath is not None else ""
        cpath = cpath.rstrip(os.sep)
        if not cwd.endswith(cpath):
            cwd = os.path.join(cwd, cpath)
            nos = Nos(cwd)
            if not nos.exists():
                nos.makedirs()
        #
        # pick and copy
        #
        path = FileCollector.select_file(
            parent=self,
            cwd=cwd,
            title="Select File",
            file_type_filter=afilter
        )
        print(f"welcome: on_click_copy_in: path: {path}")

    def on_click_run(self) -> None:
        #self.main.sidebar_rt_top._new_run()
        self._new_run()

    def _new_run(self) -> None:
        self.new_run_dialog = NewRunDialog(parent=self)
        self.new_run_dialog.show_dialog()

    def on_click_find_data_help(self) -> None:
        md = HelpFinder(main=self.main).help("find_file_by_reference_dialog/help.md")
        if md is None:
            self.main.helper.close_help()
            return
        self.main.helper.get_help_tab().setMarkdown(md)
        if not self.main.helper.is_showing_help():
            self.main.helper.on_click_help()

    def on_click_find_data(self) -> None:
        find = FindFileByReferenceDialog(main=self.main)
        find.show()

    def on_click_validate(self) -> None:
        csvpath = FileCollector.select_file(
            parent=self,
            cwd=self.main.state.cwd,
            title="Select CsvPath Language File",
            file_type_filter=FileCollector.csvpaths_filter(self.main.csvpath_config)
        )
        if csvpath is None:
            return
        #
        # how do we open and run a single csvpath from this file?
        #
        self.selected_file_path = csvpath
        self._run_one_time = csvpath
        self.main.read_validate_and_display_file_for_path(path=csvpath, editable=True, finished_callback=self._on_run_one_load)

    def _on_run_one_load(self) -> None:
        csvpath = self._run_one_time
        print(f"welcome._on_run_one_load: looking for: {csvpath}")
        #
        # iterate content's tabs to find one with widget.objectName() == csvpath
        #
        w = taut.find_tab(self.main.content.tab_widget, csvpath)
        #
        # w should be a csvpath viewer
        #
        #
        # this is probably still useful. not sure if best way.
        #
        with DataFileReader(csvpath) as file:
            csvpath = file.read()
        cs = csvpath.split("---- CSVPATH ----")
        if len(cs) > 1:

            confirm = QMessageBox.question(
                self,
                "Multiple statements",
                f"The file has multiple cvspaths. Do you want to run the first one?",
                QMessageBox.Yes | QMessageBox.No,
            )
            if confirm == QMessageBox.No:
                return
            #
            # in some cases we see ---- CSVPATH ---- coming before every csvpath
            # making the 0th csvpath empty
            #
            if cs[0].strip() == "":
                cs[0] = cs[1]
        #self.main.content.csvpath_source_view.run_one_csvpath(cs[0], None)
        print(f"welcome._on_run_one_load: cs: {cs}")
        w[1].run_one_csvpath(cs[0], None)


    def on_click_copy_in_help(self) -> None:
        md = HelpFinder(main=self.main).help("welcome/copy_in.md")
        self.main.helper.get_help_tab().setMarkdown(md)
        if not self.main.helper.is_showing_help():
            self.main.helper.on_click_help()

    def on_click_run_help(self) -> None:
        md = HelpFinder(main=self.main).help("welcome/run.md")
        self.main.helper.get_help_tab().setMarkdown(md)
        if not self.main.helper.is_showing_help():
            self.main.helper.on_click_help()

    def on_click_validate_help(self) -> None:
        md = HelpFinder(main=self.main).help("welcome/validate.md")
        self.main.helper.get_help_tab().setMarkdown(md)
        if not self.main.helper.is_showing_help():
            self.main.helper.on_click_help()

    def _copy_in_button(self, *, on_click, on_help) -> QWidget:
        self.button_copy_in = QPushButton()
        self.button_copy_in.setStyleSheet("QPushButton { width:170px;}")
        box = HelpIconPackager.add_help(main=self.main, widget=self.button_copy_in, on_help=on_help)
        self.button_copy_in.setText("Copy data in")
        self.button_copy_in.clicked.connect(on_click)
        return box

    def _run_button(self, *, on_click, on_help) -> QWidget:
        self.button_run = QPushButton()
        self.button_run.setStyleSheet("QPushButton { width:170px;}")
        box = HelpIconPackager.add_help(main=self.main, widget=self.button_run, on_help=on_help)
        self.button_run.setText("Trigger a run")
        self.button_run.clicked.connect(on_click)
        return box

    def _find_data_button(self, *, on_click, on_help) -> QWidget:
        self.button_find_data = QPushButton()
        self.button_find_data.setStyleSheet("QPushButton { width:170px;}")
        box = HelpIconPackager.add_help(main=self.main, widget=self.button_find_data, on_help=on_help)
        self.button_find_data.setText("Find data")
        self.button_find_data.clicked.connect(on_click)
        return box


    def _validate_button(self, *, on_click, on_help) -> QWidget:
        self.button_validate = QPushButton()
        self.button_validate.setStyleSheet("QPushButton { width:170px;}")
        box = HelpIconPackager.add_help(main=self.main, widget=self.button_validate, on_help=on_help)
        self.button_validate.setText("Valdiate a file")
        self.button_validate.clicked.connect(on_click)
        return box

    def on_click(self) -> None:
        ss = self.main.main.sizes()
        if ss[1] > 0:
            self.main.main.setSizes([1, 0])
        else:
            self.main.main.setSizes([4, 1])


    clicked = Signal()
    def mousePressEvent(self, event):
        self.clicked.emit()
        super().mousePressEvent(event)




