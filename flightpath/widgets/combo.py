from PySide6.QtWidgets import QComboBox


class NoWheelComboBox(QComboBox):
    """QComboBox that disables the mouse wheel event.

    The current UX when scrolling through FieldsForms is not ideal since as soon as
    the mouse points a QComboBox the form stops scrolling and it starts changing the
    value of the QComboBox instead.
    """
    def wheelEvent(self, event):
        event.ignore()


