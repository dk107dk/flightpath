from PySide6.QtWidgets import QTabBar
from PySide6.QtCore import QEvent

class NonScrollingTabBar(QTabBar):
    def wheelEvent(self, event):
        event.ignore()

