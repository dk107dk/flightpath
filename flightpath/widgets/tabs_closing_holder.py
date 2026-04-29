from PySide6.QtWidgets import QWidget


class ClosingTabsHolder(QWidget):
    def __init__(self, *, parent, can_have_edit_tabs: bool = False) -> None:
        super().__init__(parent)
        self.my_parent = parent
        self.can_have_edit_tabs = can_have_edit_tabs

    def modified(self, widget: QWidget) -> bool:
        #
        # a ClosingTabsHolder that doesn't concern itself with saving modified
        # tabs doesn't have do_i_close and modified
        #
        return False

    def do_i_close(self, t) -> bool:
        #
        # a ClosingTabsHolder that doesn't concern itself with saving modified
        # tabs doesn't have do_i_close and modified
        #
        return not self.modified
