
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QStackedLayout,
    QTabWidget,
    QMessageBox,
    QTabBar
)

from flightpath.widgets.panels.csvpath_viewer import CsvpathViewer
from flightpath.widgets.tab_overlay import TabWidgetOverlayButton
from flightpath.widgets.tabs_closing import ClosingTabs
from flightpath.widgets.toolbars.data_toolbar import DataToolbar

class Content(QWidget):

    def __init__(self, main):
        super().__init__()
        self.main = main
        layout = QVBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        self.tab_widget = ClosingTabs(main)
        layout.setContentsMargins(1, 3, 1, 2)

        TabWidgetOverlayButton(self.tab_widget, self, main)

        layout.addWidget(self.tab_widget)
        self.setLayout(layout)

        self.toolbar = DataToolbar(parent=main)

    def csvpath_files_are_saved(self) -> bool:
        for i in range(self.tab_widget.count()):
            widget = self.tab_widget.widget(i)
            if isinstance(widget, CsvpathViewer) and not widget.saved:
                return False
        return True

    def do_i_close(self, i:int) -> bool:
        widget = self.tab_widget.widget(i)
        if isinstance(widget, CsvpathViewer) and not widget.saved:
            #
            # bring tab into view
            #
            self.tab_widget.setTabVisible(i, True)
            self.tab_widget.setCurrentIndex(i)
            self.main.main_layout.setCurrentIndex(1)
            #
            # confirm
            #
            path = widget.objectName()
            if path.startswith(self.main.state.cwd):
                path = path[len(self.main.state.cwd) + 1:]
            confirm = QMessageBox.question(
                self,
                "Close file",
                f"Close {path} without saving?",
                QMessageBox.Yes | QMessageBox.No,
            )
            if confirm == QMessageBox.No:
                return False
        return True

    def close_all_tabs(self):
        #
        # if we're in a csvpath file that has changes we need to confirm we're discarding the changes
        #
        for i in range(self.tab_widget.count()):
            if not self.tab_widget.close_tab(i):
                return False
        self.main.main_layout.setCurrentIndex(0)
        return True

