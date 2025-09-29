from PySide6.QtWidgets import QMessageBox, QWidget, QInputDialog
from PySide6.QtCore import QSize, Qt

class MessageUtility:

    @classmethod
    def message(cls, *, msg:str, title:str="", icon:str=None) -> None:
        if icon is None:
            icon = QMessageBox.Critical
        if title is None:
            title = "Attention"
        msg_box = QMessageBox()
        msg_box.setIcon(icon)
        msg_box.setWindowTitle(title)
        msg_box.setText(msg)
        msg_box.setStandardButtons(QMessageBox.Ok)
        msg_box.exec()


    @classmethod
    def yes_no(cls, *, parent:QWidget, msg:str, title:str="") -> bool:
        return cls.yesNo(parent=parent, msg=msg, title=title)

    @classmethod
    def yesNo(cls, *, parent:QWidget, msg:str, title:str="") -> bool:
        box = QMessageBox(parent)
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
        ret = box.exec()
        ret = ret == QMessageBox.Yes
        return ret

    @classmethod
    def warning(cls, *, parent:QWidget, msg:str, title:str="") -> None:
        if title is None:
            title = "Warning"
        QMessageBox.warning(parent, title, msg)

    @classmethod
    def input(cls, *, msg:str, title:str="", width:int=420, height:int=125, text:str=None) -> tuple:
        dialog = QInputDialog()
        dialog.setFixedSize(QSize(420, 125))
        dialog.setLabelText(msg)
        dialog.setWindowTitle(title)
        if text is not None:
            dialog.setTextValue(text)
        ok = dialog.exec()
        text = dialog.textValue()
        return (text, ok)


