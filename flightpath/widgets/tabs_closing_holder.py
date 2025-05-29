
from PySide6.QtWidgets import QWidget
from flightpath.widgets.tabs_closing import ClosingTabs

class ClosingTabsHolder(QWidget):

    def __init__(self, *, can_have_edit_tabs:bool=False) -> None:
        super().__init__()
        self.can_have_edit_tabs = can_have_edit_tabs


