from PySide6.QtGui import QKeyEvent
from PySide6.QtCore import Qt


class KeyUtility:
    @classmethod
    def is_edit_key(cls, event: QKeyEvent) -> bool:
        ret = True
        if event is None:
            ret = False
        elif event.modifiers() != Qt.KeyboardModifier.NoModifier:
            ret = False
        elif event.key() == Qt.Key_Escape:
            ret = False
        elif event.key() in [Qt.Key_Delete, Qt.Key_Backspace]:
            ret = True
        elif event.text() == "":
            ret = False
        return ret

    @classmethod
    def has_control_key(cls, event: QKeyEvent) -> bool:
        #
        # this detects cmd on MacOS, not ctrl.
        #
        m = event.modifiers() & Qt.ControlModifier
        ret = m and m != Qt.KeyboardModifier.NoModifier
        return ret
