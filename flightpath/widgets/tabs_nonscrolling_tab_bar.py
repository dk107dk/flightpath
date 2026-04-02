from PySide6.QtWidgets import QTabBar


class NonScrollingTabBar(QTabBar):
    def wheelEvent(self, event):
        event.ignore()
