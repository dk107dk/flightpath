import PySide6.QtCore as QtCore
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QFrame, QVBoxLayout
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, Property, QObject
from PySide6.QtGui import QColor


class TurnDot(QFrame):

    def __init__(self, *, parent=None, index:int):
        super().__init__(parent)
        self._index = index
        self.setFixedSize(12, 12)
        self._active = False
        self._apply_style()

    def _apply_style(self):
        if self._active:
            self.setStyleSheet("""
                QFrame {
                    background-color: #2563eb;
                    border-radius: 6px;
                }
            """)
        else:
            self.setStyleSheet("""
                QFrame {
                    background-color: #d1d5db;
                    border-radius: 6px;
                }
            """)

    def set_active(self, active: bool):
        self._active = active
        self._apply_style()

class AIProgressWidget(QWidget):

    def __init__(self, max_turns: int = 5, parent=None):
        super().__init__(parent)
        self._max_turns = max_turns
        self._current_turn = 0
        self.row = None
        self._setup_ui()

    def _setup_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(4)

        self.row = QHBoxLayout()
        self.row.setSpacing(8)

        self._dots: list[TurnDot] = []
        for _ in range(self._max_turns):
            dot = TurnDot(index=_)
            self._dots.append(dot)
            self.row.addWidget(dot)
            if _ >0:
                dot.hide()

        self.row.addStretch()

        self._label = QLabel("Ready…    ")
        self._label.setStyleSheet("color: #6b7280; font-size: 12px;")
        self.row.addWidget(self._label)

        outer.addLayout(self.row)

    def set_turn(self, turn: int, label: str | None = None):
        self._current_turn = turn
        for i, dot in enumerate(self._dots):
            t = i <= turn
            dot.set_active(t)
            if i == turn+1:
                self._dots[i].show()
        if label:
            self._label.setText(label)
        else:
            self._label.setText(f"{turn} of {self._max_turns}…")

    def reset(self, label: str = "Done    "):
        self._current_turn = 0
        for dot in self._dots:
            dot.set_active(False)
        self._label.setText(label)

    def complete(self, label: str = "Done    "):
        self._current_turn = 0
        for dot in self._dots:
            dot.set_active(True)
        self._label.setText(label)

    def set_thinking(self, label: str = "Thinking…"):
        self._label.setText(label)
