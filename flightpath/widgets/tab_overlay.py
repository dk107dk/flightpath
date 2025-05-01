from PySide6.QtWidgets import QApplication, QTabWidget, QTabBar, QPushButton, QVBoxLayout, QWidget, QMessageBox
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QStyle
from PySide6.QtCore import QSize, Qt

class TabWidgetOverlayButton(QWidget):
    def __init__(self, tabs, main):
        super().__init__()
        self.tabs = tabs
        self.main = main

        # Create close all button
        self.close_all_button = QPushButton()
        self.close_all_button.setStyleSheet("background-color: transparent; border: none; margin: 0 10px 5px 0;")
        pixmapi = QStyle.StandardPixmap.SP_TitleBarCloseButton
        icon = self.close_all_button.style().standardIcon(pixmapi)
        self.close_all_button.setIcon(icon)
        self.close_all_button.setIconSize(QSize(16, 16))

        # Set up layout
        layout = QVBoxLayout(self)
        layout.addWidget(self.close_all_button)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        # Connect the button's clicked signal directly
        self.close_all_button.clicked.connect(self.close_all_tabs)

        # Make the button a proper widget in the corner of the tab widget
        self.tabs.setCornerWidget(self, Qt.Corner.TopRightCorner)

    def close_all_tabs(self):
        #
        # if we're in a csvpath file that has changes we need to confirm we're discarding the changes
        #
        i = self.tabs.currentIndex()
        if i == 2 and self.main.content.csvpath_source_view.saved is not True:
            path = self.main.content.csvpath_source_view.path
            if path.startswith(self.main.state.cwd):
                path = path[len(self.main.state.cwd) + 1:]
            confirm = QMessageBox.question(
                self,
                "Close file",
                f"Close {path} without saving?",
                QMessageBox.Yes | QMessageBox.No,
            )
            if confirm == QMessageBox.No:
                return
            self.main.content.csvpath_source_view.reset_saved()
        self.main.main_layout.setCurrentIndex(0)
        #
        # close the sample toolbar, if visible
        #
        self.main.content.data_view.toolbar.hide()
        #
        # close the right tabs, if visible
        #
        self.main._rt_tabs_hide()

