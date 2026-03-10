"""
ErrorDialog - A PySide6 error dialog that mimics a native OS error dialog,
with optional expandable JSON details panel.

Usage:
    # Simple error message only
    dlg = ErrorDialog(parent, "Something went wrong.")
    dlg.exec()

    # Error message with JSON error objects
    errors = [{"code": 404, "message": "Not found"}, {"code": 500, "message": "Server error"}]
    dlg = ErrorDialog(parent, "Multiple errors occurred.", errors=errors)
    dlg.exec()
"""

import json
import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QDialogButtonBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QStyle,
    QVBoxLayout,
    QWidget,
)


class ErrorDialog(QDialog):
    """
    A native-feeling error dialog with an optional expandable JSON details panel.

    Args:
        parent:   Parent widget (can be None).
        message:  The human-readable error message to display.
        errors:   Optional list of error objects (dicts / anything JSON-serialisable).
                  When provided, a "Show Details…" button is added.
        title:    Window title. Defaults to "Error".
    """

    _DETAILS_HEIGHT = 200  # px for the JSON text area when expanded

    def __init__(self, parent=None, message: str = "", errors=None, title: str = "Error"):
        super().__init__(parent)

        self._errors = errors
        self._details_visible = False

        self.setWindowTitle(title)
        # Remove the "?" help button; keep close button only
        self.setWindowFlags(
            self.windowFlags()
            & ~Qt.WindowType.WindowContextHelpButtonHint
        )
        self.setSizeGripEnabled(False)
        self.setMinimumWidth(380)

        self._build_ui(message)
        self.adjustSize()
        self.setFixedSize(self.sizeHint())  # lock size until expansion
        #
        # exp
        #
        self.setSizeGripEnabled(True)

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self, message: str) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 12)
        root.setSpacing(0)

        # ── Top row: icon + message ────────────────────────────────────
        top = QHBoxLayout()
        top.setSpacing(14)

        icon_label = QLabel()
        style = self.style()
        icon = style.standardIcon(QStyle.StandardPixmap.SP_MessageBoxCritical, None, self)
        icon_label.setPixmap(icon.pixmap(32, 32))
        icon_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        icon_label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        top.addWidget(icon_label)

        msg_label = QLabel(message)
        msg_label.setWordWrap(True)
        msg_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        msg_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        top.addWidget(msg_label)

        root.addLayout(top)
        root.addSpacing(12)

        # ── Separator ─────────────────────────────────────────────────
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        #root.addWidget(line)
        root.addSpacing(8)

        # ── JSON details area (hidden initially) ──────────────────────
        self._details_widget = QWidget()
        details_layout = QVBoxLayout(self._details_widget)
        details_layout.setContentsMargins(0, 0, 0, 0)
        details_layout.setSpacing(4)

        details_label = QLabel("Error details:")
        details_layout.addWidget(details_label)

        self._text_area = QPlainTextEdit()
        self._text_area.setReadOnly(True)
        #
        # exp
        #
        #self._text_area.setFixedHeight(self._DETAILS_HEIGHT)
        self._text_area.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        # Monospace font for JSON readability
        font = self._text_area.font()
        font.setFamily("Courier New, Courier, monospace")
        font.setPointSize(11)
        self._text_area.setFont(font)
        if self._errors is not None:
            self._text_area.setPlainText(
                json.dumps(self._errors, indent=2, ensure_ascii=False)
            )
        details_layout.addWidget(self._text_area)
        details_layout.addSpacing(8)

        self._details_widget.setVisible(False)
        root.addWidget(self._details_widget)

        # ── Button row ────────────────────────────────────────────────
        btn_row = QHBoxLayout()
        btn_row.setSpacing(6)

        if self._errors is not None:
            self._toggle_btn = QPushButton("Show Details…")
            self._toggle_btn.setAutoDefault(False)
            self._toggle_btn.clicked.connect(self._toggle_details)
            btn_row.addWidget(self._toggle_btn)

        btn_row.addItem(QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))

        close_btn = QPushButton("Close")
        close_btn.setDefault(True)
        close_btn.clicked.connect(self.accept)
        btn_row.addWidget(close_btn)

        root.addLayout(btn_row)

    # ------------------------------------------------------------------
    # Slot
    # ------------------------------------------------------------------

    def _toggle_details(self) -> None:
        self._details_visible = not self._details_visible
        self._details_widget.setVisible(self._details_visible)
        self._toggle_btn.setText("Hide Details" if self._details_visible else "Show Details…")

        # Unlock fixed size, resize, then re-lock
        self.setFixedSize(QWIDGETSIZE_MAX, QWIDGETSIZE_MAX)
        self.adjustSize()
        #
        # exp
        #
        #self.setFixedSize(self.sizeHint())


# A large sentinel value used to "un-fix" a QWidget's size
QWIDGETSIZE_MAX = (1 << 24) - 1



