from PySide6.QtWidgets import QTabWidget, QPushButton, QStyle, QTabBar, QWidget
from PySide6.QtGui import QIcon
from PySide6.QtCore import Slot

from flightpath.widgets.panels.json_viewer import JsonViewer
from flightpath.widgets.panels.csvpath_viewer import CsvpathViewer
from flightpath.widgets.panels.data_viewer import DataViewer
#from flightpath.widgets.help.helper import Helper
from flightpath.util.tabs_utility import TabsUtility as taut

class ClosingTabs(QTabWidget):
    def __init__(self, main, *, parent=None):
        super().__init__()
        self.main = main
        #
        # if we live in content we (may) need to know it.
        # if we're the info & feedback we don't.
        #
        self.parent = parent
        self.currentChanged.connect(self.on_tab_change)

    @Slot(str)
    def close_tab(self, name:str) -> bool:
        #
        # we find tabs by name because the indexes change
        # using our own tab close icon made the changing
        # indexes difficult. and closing by file path is more
        # exact, anyway.
        #
        t = taut.find_tab(self, name)
        #
        # confirm if needed
        #
        if not self.main.content.do_i_close(t[0]):
            return False
        #
        # remove and delete
        #
        if t:
            self.removeTab(t[0])
            t[1].deleteLater()
            #
            # show and hides
            #
            self._configure_tabs()
            return True
        return False

    def close_tab_at(self, index:int) -> bool:
        #
        # this is expected to be called where needed, e.g. content's
        # close all, but not connected for UI callbacks. see the comment
        # in close_tab above.
        #
        t = self.widget(index)
        if t:
            self.removeTab(index)
            t.deleteLater()
            self._configure_tabs()
            return True
        return False

    def _configure_tabs(self) -> None:
        #
        # show and hides
        #
        if not self.has_data_tabs():
            self.main._on_data_toolbar_hide()
        if not self.has_csvpath_tabs():
            self.main._rt_tabs_hide()
        #
        # helper is responsable for the closing tabs it desplays help in
        # so we cannot use Helper directly. we could just assume any time
        # there is a parent we have a helper; checking the attr is probably
        # one better.
        #
        if self.count() == 0 and not hasattr(self.parent, "close_help"):
            self.main.main_layout.setCurrentIndex(0)
        elif self.count() == 0 and hasattr(self.parent, "close_help"):
            self.parent.close_help()
        return True


    def has_csvpath_tabs(self) -> bool:
        return taut.has_type(self, CsvpathViewer)

    def has_json_tabs(self) -> bool:
        return taut.has_type(self, JsonViewer)

    def has_data_tabs(self) -> bool:
        return taut.has_type(self, DataViewer)

    def addTab(self, widget, title):
        index = super().addTab(widget, title)
        close_button = QPushButton()
        close_button.setIcon(QIcon(self.style().standardIcon(QStyle.SP_TitleBarCloseButton)))
        close_button.setStyleSheet("border: none;")
        close_button.clicked.connect(lambda: self.close_tab(widget.objectName()))
        self.tabBar().setTabButton(index, QTabBar.ButtonPosition.LeftSide, close_button)

    def on_tab_change(self):
        i = self.currentIndex()
        w = self.widget(i)
        if w:
            path = w.objectName()
            self.main.selected_file_path = path
            self.main.statusBar().showMessage(f"  {path}")
            if isinstance(w, DataViewer):
                self.main.content.toolbar.enable()
            else:
                self.main.content.toolbar.disable()

