from PySide6.QtCore import Signal
from PySide6.QtWidgets import QLabel

class ClickableLabel(QLabel):

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

    clicked = Signal(str)



    def mousePressEvent(self, event):
        self.clicked.emit(self.text())
        event.accept()
        #
        # accept to block propagation
        #
        #super().mousePressEvent(event)

