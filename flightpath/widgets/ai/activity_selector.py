from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QWidget, QHBoxLayout, QToolButton, QButtonGroup, QSizePolicy


class ActivitySelector(QWidget):
    activityChanged = Signal(str)

    ACTIVITIES = [
        ("validation", "📄", "Create"),
        ("question", "❓", "Ask"),
        ("improve", "🔧", "Improve"),
        ("testdata", "🧪", "Data"),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setMinimumHeight(23)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.group = QButtonGroup(self)
        self.group.setExclusive(True)

        self.buttons = {}

        for key, icon, label in self.ACTIVITIES:
            btn = QToolButton(self)
            btn.setText(f"{icon}  {label}")
            btn.setCheckable(True)
            btn.setAutoExclusive(True)
            btn.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
            btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            btn.setFixedHeight(23)
            btn.setFixedWidth(74)
            layout.addWidget(btn)
            self.group.addButton(btn)
            self.buttons[key] = btn
        layout.addStretch(1)

        self.buttons["validation"].setChecked(True)

        self.group.buttonClicked.connect(self._on_clicked)

    def _on_clicked(self, btn):
        for key, b in self.buttons.items():
            if b is btn:
                self.activityChanged.emit(key)
                break

    def setActivity(self, key: str):
        if key in self.buttons:
            self.buttons[key].setChecked(True)

