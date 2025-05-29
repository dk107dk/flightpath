
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QStackedLayout,
    QTabWidget,
    QMessageBox,
    QTabBar
)
from PySide6.QtCore import Slot

from flightpath.widgets.panels.csvpath_viewer import CsvpathViewer
from flightpath.widgets.panels.json_viewer import JsonViewer
from flightpath.widgets.tab_overlay import TabWidgetOverlayButton
from flightpath.widgets.tabs_closing import ClosingTabs
from flightpath.widgets.tabs_closing_holder import ClosingTabsHolder
from flightpath.widgets.toolbars.data_toolbar import DataToolbar

class Content(ClosingTabsHolder):

    def __init__(self, main):
        super().__init__(can_have_edit_tabs=True)
        self.main = main
        layout = QVBoxLayout()
        layout.setSpacing(0)
        # we reset the margins below. is there a reason to do it here too?
        layout.setContentsMargins(0, 0, 0, 0)

        self.tab_widget = ClosingTabs(main, parent=self)
        TabWidgetOverlayButton(self.tab_widget, self, main)
        layout.addWidget(self.tab_widget)
        layout.setContentsMargins(1, 3, 1, 2)

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
        ret = True
        close = []
        for i in range(self.tab_widget.count()):
            widget = self.tab_widget.widget(i)
            if self.do_i_close(i):
                name = widget.objectName()
                close.append(name)
            else:
                ret = False
        #print(f"close_all_tabs: ret: {ret}, close: {close}")
        for widget in self.tab_widget.findChildren(QWidget):
            #print(f"close_all_tabs: widget: {widget}")
            #print(f"close_all_tabs: widget: {widget.objectName()}")
            name = widget.objectName()
            if name in close:
                i = self.tab_widget.indexOf(widget)
                self.tab_widget.close_tab_at(i)
                close.remove(name)
                widget.deleteLater()
        if ret:
            #
            # set to welcome
            #
            self.main.main_layout.setCurrentIndex(0)
        return ret

