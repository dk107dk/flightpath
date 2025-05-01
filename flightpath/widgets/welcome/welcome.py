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
    QTextBrowser,
    QSpacerItem,
    QFileDialog,
    QInputDialog,
    QMessageBox
)

from csvpath.util.file_readers import DataFileReader
from csvpath.util.file_writers import DataFileWriter

from flightpath.widgets.clickable_label import ClickableLabel
from flightpath.widgets.plus_help import HelpIconPackager
from flightpath.util.help_finder import HelpFinder
from flightpath.util.file_utility import FileUtility as fiut
from flightpath.util.file_collector import FileCollector

class Welcome(QWidget):

    def __init__(self, main):
        super().__init__()
        self.main = main
        self.button_copy_in = None
        main_layout = QVBoxLayout()
        main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        image_label = QLabel(self)
        pixmap = QPixmap(fiut.make_app_path(f"assets{os.sep}images{os.sep}flightpath-gray.svg"))
        image_label.setPixmap(pixmap)
        image_label.setAlignment(Qt.AlignCenter)

        #
        # these boxes have a button + help icon
        #
        self.copy_in_box = self._copy_in_button(on_click=self.on_click_copy_in, on_help=self.on_click_copy_in_help)
        self.run_box = self._run_button(on_click=self.on_click_run, on_help=self.on_click_run_help)
        self.validate_box = self._validate_button(on_click=self.on_click_validate, on_help=self.on_click_validate_help)

        top_layout = QVBoxLayout()
        top_layout.addWidget(image_label)
        top_layout.addWidget(self.copy_in_box)
        top_layout.addWidget(self.run_box)
        top_layout.addWidget(self.validate_box)
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


    def on_click_copy_in(self) -> None:
        csvps = FileCollector.csvpaths_filter(self.main.csvpath_config)
        csvs = FileCollector.csvs_filter(self.main.csvpath_config)
        afilter = f"{csvps};;{csvs}"

        path = FileCollector.select_file(
            parent=self,
            cwd=self.main.state.cwd,
            title="Select File",
            filter=afilter
        )
        print(f"welcome: on_click_copy_in: path: {path}")

    def on_click_run(self) -> None:
        self.main.sidebar_rt_top._new_run()

    def on_click_validate(self) -> None:
        csvpath = FileCollector.select_file(
            parent=self,
            cwd=self.main.state.cwd,
            title="Select CsvPath Language File",
            filter=FileCollector.csvpaths_filter(self.main.csvpath_config)
        )
        print(f"welcome: on_click_validate: csvpath path: {csvpath}")
        if csvpath is None:
            return
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
        self.main.content.csvpath_source_view.run_one_csvpath(cs[0], None)

    def on_click_copy_in_help(self) -> None:
        md = HelpFinder(main=self.main).help("welcome/copy_in.md")
        #self.main.help.setMarkdown(md)
        self.main.get_help_tab().setMarkdown(md)
        if not self.main.is_showing_help():
            self.main.on_click_help()



    def on_click_run_help(self) -> None:
        md = HelpFinder(main=self.main).help("welcome/run.md")
        #self.main.help.setMarkdown(md)
        self.main.get_help_tab().setMarkdown(md)
        if not self.main.is_showing_help():
            self.main.on_click_help()

    def on_click_validate_help(self) -> None:
        md = HelpFinder(main=self.main).help("welcome/validate.md")
        self.main.get_help_tab().setMarkdown(md)
        """
        if self.main.help:
            for i in range(self.main.help_and_feedback.count()):
                if self.main.help_and_feedback.tabText(i) == "Help Content":
                    self.main.help_and_feedback.removeTab(i)
                return -1
            self.main.help.deleteLater()
            self.main.help = None
            self.main.self.assure_help_tab()
        print(f"on_click_validate_help: main: {self.main}")
        print(f"on_click_validate_help: help: {self.main.help}")
        print(f"on_click_validate_help: md: {md}")
        self.main.help.setMarkdown(md)
        """
        if not self.main.is_showing_help():
            self.main.on_click_help()

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




