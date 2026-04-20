from PySide6.QtWidgets import QMessageBox, QWidget, QInputDialog
from PySide6.QtCore import QSize, Qt

from flightpath.dialogs.error_dialog import ErrorDialog


class MessageUtility:
    @classmethod
    def message(
        cls, *, parent: QWidget, msg: str, title: str = "", icon: str = None
    ) -> None:
        if icon is None:
            icon = QMessageBox.Critical
        if title is None:
            title = "Attention"
        box = QMessageBox(parent=parent)
        box.setWindowFlags(
            Qt.Dialog
            | Qt.WindowTitleHint
            | Qt.WindowSystemMenuHint
            | Qt.WindowStaysOnTopHint
        )
        box.setIcon(icon)
        box.setWindowTitle(title)
        box.setText(msg)
        box.setStandardButtons(QMessageBox.Ok)
        box.show()
        box.raise_()
        box.activateWindow()
        box.exec()

    @classmethod
    def error(
        cls, *, parent: QWidget, msg: str, title: str = "", errors_json=None
    ) -> None:
        box = ErrorDialog(parent=parent, message=msg, title=title, errors=errors_json)
        box.setWindowFlags(
            Qt.Dialog
            | Qt.WindowTitleHint
            | Qt.WindowSystemMenuHint
            | Qt.WindowStaysOnTopHint
        )
        box.show()
        box.raise_()
        box.activateWindow()
        box.exec()

    @classmethod
    def yes_no(cls, *, parent: QWidget, msg: str, title: str = "") -> bool:
        return cls.yesNo(parent=parent, msg=msg, title=title)

    @classmethod
    def yesNo(cls, *, parent: QWidget, msg: str, title: str = "") -> bool:
        box = QMessageBox(parent=parent)
        box.setText(title)
        box.setInformativeText(msg)
        box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        box.setDefaultButton(QMessageBox.No)
        #
        # this line fixed what seems to have been a modality problem. it unblocks the
        # ui but also gives yet another (3rd?) slightly different style of input/message
        # dialog. also shadows the whole of FlightPath in a way we don't do elsewhere.
        #
        # TODO: long-term we should figure out how to be consistent.
        # it would also be nice to know why we had the problem. There's more information
        # and suggestions to try re: the bug in Copilot from 29 sept 2025.
        #
        box.setWindowModality(Qt.WindowModal)
        box.setWindowFlags(
            Qt.Dialog
            | Qt.WindowTitleHint
            | Qt.WindowSystemMenuHint
            | Qt.WindowStaysOnTopHint
        )
        box.show()
        box.raise_()
        box.activateWindow()
        ret = box.exec()
        ret = ret == QMessageBox.Yes
        return ret

    @classmethod
    def warning(cls, *, parent: QWidget, msg: str, title: str = "") -> None:
        if title is None:
            title = "Warning"
        QMessageBox.warning(parent, title, msg)

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
        box.setWindowFlags(
            Qt.Dialog
            | Qt.WindowTitleHint
            | Qt.WindowSystemMenuHint
            | Qt.WindowStaysOnTopHint
        )
        box.show()
        box.raise_()
        box.activateWindow()
        ok = box.exec()
        text = box.textValue()
        return (text, ok)
