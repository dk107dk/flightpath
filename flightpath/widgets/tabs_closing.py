from PySide6.QtWidgets import QTabWidget, QPushButton, QStyle, QTabBar, QWidget
from PySide6.QtGui import QIcon
from PySide6.QtCore import Slot

from flightpath.widgets.panels.json_viewer import JsonViewer
from flightpath.widgets.panels.csvpath_viewer import CsvpathViewer
from flightpath.widgets.panels.data_viewer import DataViewer

from flightpath.util.tabs_utility import TabsUtility as taut

class ClosingTabs(QTabWidget):
    def __init__(self, main):
        super().__init__()
        self.main = main
        self.tabCloseRequested.connect(self.close_tab)
        self.currentChanged.connect(self.on_tab_change)
        self.index = {}

    @Slot(int)
    def close_tab(self, index) -> bool:
        current = self.currentIndex()
        if not self.main.content.do_i_close(current):
            return False
        #
        # set the nearest tab as selected, if any tabs
        #
        if index == current and self.count() > 1:
            self.setCurrentIndex(current - 1)
        #
        #
        #
        name = self.index.get(index)
        t = self.findChild(QWidget, name)
        if t:
            i = self.indexOf(t)
            self.removeTab(i)
            t.deleteLater()
            if index in self.index:
                del self.index[index]
            else:
                print(f"closing tabs: close tab: why is {index} not in {self.index}?")
        if self.count() == 0:
            print("we need to close helpx here if this is help")
        if not self.has_data_tabs():
            self.main._on_data_toolbar_hide()
        if not self.has_csvpath_tabs():
            self.main._rt_tabs_hide()
        if self.count() == 0:
            self.main.show_welcome_screen()
        return True

    def has_csvpath_tabs(self) -> bool:
        return taut.has_type(self, CsvpathViewer)

    def has_json_tabs(self) -> bool:
        return taut.has_type(self, JsonViewer)

    def has_data_tabs(self) -> bool:
        return taut.has_type(self, DataViewer)

    def addTab(self, widget, title):
        index = super().addTab(widget, title)
        #
        # exp. can we use a map to find the title given the original index
        # with the title find the current index.
        #
        self.index[index] = title if widget.objectName() is None else widget.objectName()
        close_button = QPushButton()
        close_button.setIcon(QIcon(self.style().standardIcon(QStyle.SP_TitleBarCloseButton)))
        close_button.setStyleSheet("border: none;")
        close_button.clicked.connect(lambda: self.close_tab(index))
        self.tabBar().setTabButton(index, QTabBar.ButtonPosition.LeftSide, close_button)


    def on_tab_change(self):
        i = current = self.currentIndex()
        w = self.widget(i)
        if w:
            path = w.objectName()
            self.main.selected_file_path = path
            self.main.statusBar().showMessage(f"  {path}")
            if isinstance(w, DataViewer):
                self.main.content.toolbar.enable()
            else:
                self.main.content.toolbar.disable()

