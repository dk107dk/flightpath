from typing import Callable

from PySide6.QtWidgets import QMessageBox, QWidget, QInputDialog, QDialog
from PySide6.QtCore import QSize

from flightpath.dialogs.error_dialog import ErrorDialog


class MessageUtility:
    @classmethod
    def message2(
        cls,
        *,
        parent: QWidget,
        msg: str,
        title: str = "",
        icon: str = None,
        callback: Callable = None,
        args: dict = None,
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
        args = {} if args is None else args

        def finished():
            callback(**args)

        if callback is not None:
            box.finished.connect(finished)
            box.deleteLater()
        box.show()

    @classmethod
    def warning2(
        cls,
        *,
        parent: QWidget,
        msg: str,
        title: str = "",
        icon: str = None,
        callback: Callable = None,
        args: dict = None,
    ) -> None:
        cls.message2(
            parent=parent, msg=msg, title=title, icon=icon, callback=callback, args=args
        )

    @classmethod
    def errors2(
        cls,
        *,
        parent: QWidget,
        msg: str,
        title: str = "",
        errors: dict | list = None,
        callback: Callable = None,
    ) -> None:
        box = ErrorDialog(parent=parent, message=msg, title=title, errors=errors)
        if callback is not None:
            box.finished.connect(callback)
            box.deleteLater()
        box.show()

    @classmethod
    def input2(
        cls,
        *,
        parent: QWidget,
        msg: str,
        title: str = "",
        width: int = 420,
        height: int = 125,
        text: str = None,
        callback: Callable,
        args: dict = None,
    ) -> None:
        args = {} if args is None else args
        box = QInputDialog(parent)
        box.setFixedSize(QSize(width, height))
        box.setLabelText(msg)
        box.setWindowTitle(title)
        if text is not None:
            box.setTextValue(text)

        def finished(result: int) -> tuple[str, bool]:
            ok = result == QDialog.Accepted
            value = box.textValue()
            callback((value, ok), **args)
            box.deleteLater()

        box.finished.connect(finished)
        box.open()

    @classmethod
    def yesNo2(
        cls,
        *,
        parent: QWidget,
        callback: Callable,
        msg: str,
        title: str = "",
        args=None,
    ) -> int:
        box = QMessageBox(parent)
        box.setText(title)
        box.setInformativeText(msg)
        box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        box.setDefaultButton(QMessageBox.No)
        args = {} if args is None else args

        def finished(r: int):
            callback(r, **args)
            box.deleteLater()

        box.finished.connect(finished)
        box.open()

    # ============================================================
    # old exec ways
    #

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
        box.show()

    @classmethod
    def warning(cls, *, parent: QWidget, msg: str, title: str = "") -> None:
        #
        # for now, during cleanup, nothing different
        #
        cls.message(parent=parent, msg=msg, title=title)

    @classmethod
    def error(
        cls, *, parent: QWidget, msg: str, title: str = "", errors_json=None
    ) -> None:
        #
        # for now, during cleanup, nothing different
        #
        cls.message(parent=parent, msg=msg, title=title)

    # ===================================

    """
    @classmethod
    def yesNo(cls, *, parent: QWidget, callback:Callable, msg: str, title: str = "") -> bool:
        box = QMessageBox(parent)
        box.setText(title)
        box.setInformativeText(msg)
        box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        box.setDefaultButton(QMessageBox.No)
        # cls._z(box)
        box.finished.connect(callback)
        ret = box.open()
    """

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
