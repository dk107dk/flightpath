from PySide6.QtWidgets import QMessageBox, QWidget, QInputDialog
from PySide6.QtCore import QSize, Qt
from PySide6.QtCore import QTimer

from flightpath.dialogs.error_dialog import ErrorDialog


class MessageUtility:
    @classmethod
    def _z(cls, box) -> None:
        box.setWindowModality(Qt.ApplicationModal)
        box.setWindowFlags(
            box.windowFlags() | Qt.WindowTitleHint | Qt.WindowSystemMenuHint
            # Remove WindowStaysOnTopHint — let ApplicationModal handle exclusivity
        )
        QTimer.singleShot(0, box.raise_)
        QTimer.singleShot(0, box.activateWindow)

    @classmethod
    def message(
        cls, *, parent: QWidget, msg: str, title: str = "", icon: str = None
    ) -> None:
        if icon is None:
            icon = QMessageBox.Critical
        if title is None:
            title = "Attention"
        box = QMessageBox(parent=parent)
        box.setIcon(icon)
        box.setWindowTitle(title)
        box.setText(msg)
        box.setStandardButtons(QMessageBox.Ok)
        cls._z(box)
        box.exec()

    @classmethod
    def warning(cls, *, parent: QWidget, msg: str, title: str = "") -> None:
        if title is None:
            title = "Warning"
        QMessageBox.warning(parent, title, msg)

    @classmethod
    def error(
        cls, *, parent: QWidget, msg: str, title: str = "", errors_json=None
    ) -> None:
        box = ErrorDialog(parent=parent, message=msg, title=title, errors=errors_json)
        cls._z(box)
        box.exec()

    @classmethod
    def yes_no(cls, *, parent: QWidget, msg: str, title: str = "") -> bool:
        return cls.yesNo(parent=parent, msg=msg, title=title)

    @classmethod
    def yesNo(cls, *, parent: QWidget, msg: str, title: str = "") -> bool:
        box = QMessageBox()  # parent=parent
        box.setText(title)
        box.setInformativeText(msg)
        box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        box.setDefaultButton(QMessageBox.No)
        # cls._z(box)
        ret = box.exec()
        ret = ret == QMessageBox.Yes
        return ret

    # return cls.yesNoButtons(parent=parent, msg=msg, title=title, std_buttons=std_buttons)

    @classmethod
    def yesNoButtons(
        cls,
        *,
        parent: QWidget,
        msg: str,
        title: str = "",
        std_buttons=None,
        truth_button=QMessageBox.Yes,
        def_button=QMessageBox.No,
    ) -> bool:
        if std_buttons is None:
            std_buttons = QMessageBox.Yes | QMessageBox.No
        box = QMessageBox(parent=parent)
        box.setText(title)
        box.setInformativeText(msg)
        box.setStandardButtons(std_buttons)
        box.setDefaultButton(def_button)
        cls._z(box)
        ret = box.exec()
        ret = ret == truth_button
        return ret

    @classmethod
    def input(
        cls,
        *,
        parent: QWidget,
        msg: str,
        title: str = "",
        width: int = 420,
        height: int = 125,
        text: str = None,
    ) -> tuple:
        box = QInputDialog(parent=parent)
        box.setFixedSize(QSize(420, 125))
        box.setLabelText(msg)
        box.setWindowTitle(title)
        if text is not None:
            box.setTextValue(text)
        cls._z(box)
        ok = box.exec()
        text = box.textValue()
        return (text, ok)
