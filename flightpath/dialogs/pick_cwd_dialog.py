import os

from PySide6.QtWidgets import ( # pylint: disable=E0611
        QWidget,
        QVBoxLayout,
        QHBoxLayout,
        QPushButton,
        QLabel,
        QFileDialog,
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
        #self.cancel_button.clicked.connect(self.reject)
        right_side.layout().addWidget(self.cancel_button)

        build_number = fiut.read_string(fiut.make_app_path(f"assets{os.sep}build_number.txt")).strip()
        bn = QLabel(build_number)
        bn.setStyleSheet("QLabel {font-size:10px;color:#999}")
        bn.setFixedHeight(11)
        right_side.layout().addWidget(bn)

    def _cancel(self) -> bool:
        #self.main.show()
        self.reject()

    def _pick_cwd(self) -> bool:
        path = QFileDialog.getExistingDirectory(self.main, "FlightPath requires a project directory. Please pick one.")
        if path:
            self.main.state.cwd = path
            self.main.state.load_state_and_cd(self.main)
            self.main.statusBar().showMessage(f"  Working directory changed to: {path}")
        #
        # reject dismisses the dialog and we exit the app. we could
        # just return.
        #
        #self.main.show()
        self.reject()

    def show_dialog(self) -> None:
        self.exec()
