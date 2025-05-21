import os
from pathlib import Path

from PySide6.QtWidgets import ( # pylint: disable=E0611
        QWidget,
        QVBoxLayout,
        QHBoxLayout,
        QPushButton,
        QLabel,
        QMessageBox,
        QDialog
)
from PySide6.QtCore import Qt # pylint: disable=E0611
from PySide6.QtGui import QPixmap, QPainter

from csvpath.util.nos import Nos

from flightpath.util.file_utility import FileUtility as fiut


class PickCwdDialog(QDialog):

    def __init__(self,main):
        super().__init__(main)
        self.main = main
        self.main.hide()
        self.setWindowTitle("Please pick a project directory")

        self.errors = None
        self.template = None
        self.named_paths_name = None
        self.recurse = True

        self.setFixedHeight(300)
        self.setFixedWidth(500)

        main_layout = QHBoxLayout()
        self.setLayout(main_layout)
        self.setWindowModality(Qt.ApplicationModal)

        left_side = QWidget()
        left_side.setLayout(QVBoxLayout())
        image_label = QLabel(self)
        pixmap = QPixmap(fiut.make_app_path(f"assets{os.sep}images{os.sep}flightpath-gray.svg"))
        image_label.setPixmap(pixmap)
        image_label.setAlignment(Qt.AlignCenter)
        left_side.layout().addWidget(image_label)

        right_side = QWidget()
        right_side.setLayout(QVBoxLayout())

        main_layout.addWidget(left_side)
        main_layout.addWidget(right_side)

        lab = QLabel()
        lab.setText("FlightPath requires a project directory. It will create a few configuration assets there to get you started.")
        lab.setWordWrap(True)
        lab.setStyleSheet("QLabel {font-weight:500; font-size:16pt;}")

        self.load_button = QPushButton()
        self.load_button.setDefault(True)
        self.load_button.setText(self.tr("Pick one now?"))
        self.load_button.clicked.connect(self._pick_cwd)
        right_side.layout().addWidget(lab)
        right_side.layout().addWidget(self.load_button)

        self.cancel_button = QPushButton()
        self.cancel_button.setText(self.tr("Come back later"))
        self.cancel_button.clicked.connect(self._cancel)
        right_side.layout().addWidget(self.cancel_button)

        build_number = fiut.read_string(fiut.make_app_path(f"assets{os.sep}build_number.txt")).strip()
        bn = QLabel(build_number)
        bn.setStyleSheet("QLabel {font-size:10px;color:#999}")
        bn.setFixedHeight(11)
        right_side.layout().addWidget(bn)

    def _cancel(self) -> bool:
        self.reject()

    def _pick_cwd(self) -> bool:
        """
        caption = "FlightPath requires a project directory. Please pick one."
        home = str(Path.home())
        path = QFileDialog.getExistingDirectory(
            parent=self,
            caption=caption,
            dir=home,
            options=QFileDialog.Option.DontUseNativeDialog,
        )
        if path:
            if self.main.is_writable(path):
                print(f"pick_cwd_dialog: _pick_cwd: {path} is writable")
                self.main.state.cwd = path
            else:
                print(f"pick_cwd_dialog: _pick_cwd: {path} is not writable")
                msg_box = QMessageBox()
                msg_box.setIcon(QMessageBox.Critical)
                msg_box.setWindowTitle("Not writable")
                msg_box.setText(f"{path} is not a writable location. Please pick another.")
                msg_box.setStandardButtons(QMessageBox.Ok)
                msg_box.exec()
                self._pick_cwd()
        """
        self.main.on_set_cwd_click()
        #
        # closes dialog, not app
        #
        self.reject()


    def show_dialog(self) -> None:
        self.exec()
