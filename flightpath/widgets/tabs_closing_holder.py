from PySide6.QtWidgets import QWidget


class ClosingTabsHolder(QWidget):
    def __init__(self, *, parent, can_have_edit_tabs: bool = False) -> None:
        super().__init__(parent)
        self.my_parent = parent
        self.can_have_edit_tabs = can_have_edit_tabs
