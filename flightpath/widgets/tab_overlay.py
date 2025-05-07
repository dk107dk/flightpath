from PySide6.QtWidgets import QTabWidget, QPushButton, QVBoxLayout, QWidget
from PySide6.QtWidgets import QStyle
from PySide6.QtCore import QSize, Qt

class TabWidgetOverlayButton(QWidget):
    def __init__(self, tabs, parent, main):
        super().__init__()
        self.tabs = tabs
        self.main = main
        self.parent = parent

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
        self.close_all_button.clicked.connect(self.parent.close_all_tabs)

        # Make the button a proper widget in the corner of the tab widget
        self.tabs.setCornerWidget(self, Qt.Corner.TopRightCorner)

