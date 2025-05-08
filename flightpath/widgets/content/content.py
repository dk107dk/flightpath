
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QStackedLayout,
    QTabWidget,
    QMessageBox,
    QTabBar
)

from flightpath.widgets.panels.csvpath_viewer import CsvpathViewer
from flightpath.widgets.panels.json_viewer import JsonViewer
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

        self.tab_widget = ClosingTabs(main, parent=self)
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

    def json_files_are_saved(self) -> bool:
        for i in range(self.tab_widget.count()):
            widget = self.tab_widget.widget(i)
            if isinstance(widget, JsonViewer) and widget.modified:
                return False
        return True

    def all_files_are_saved(self) -> bool:
        return self.csvpath_files_are_saved() and self.json_files_are_saved()

    def do_i_close(self, i:int) -> bool:
        widget = self.tab_widget.widget(i)
        cmod = isinstance(widget, CsvpathViewer) and not widget.saved
        jmod = isinstance(widget, JsonViewer) and widget.modified
        mod = cmod or jmod
        if mod:
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
        while self.tab_widget.count() > 0:
            if not self.tab_widget.close_tab(0):
                print(f"content: cannot close tab @ 0!")
                return False
        #
        # set to welcome
        #
        self.main.main_layout.setCurrentIndex(0)
        return True

