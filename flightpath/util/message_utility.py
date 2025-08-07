from PySide6.QtWidgets import QMessageBox, QWidget, QInputDialog
from PySide6.QtCore import QSize

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
    def yesNo(cls, *, parent:QWidget, msg:str, title:str="") -> bool:
        confirm = QMessageBox.question(
            parent,
            title,
            msg,
            QMessageBox.Yes | QMessageBox.No,
        )
        return confirm == QMessageBox.Yes


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


