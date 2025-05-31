import os

from PySide6.QtWidgets import QTabWidget, QPushButton, QStyle, QTabBar, QWidget, QMenu
from PySide6.QtGui import QIcon, QAction
from PySide6.QtCore import Slot, Qt

from csvpath.util.nos import Nos

from flightpath.widgets.panels.json_viewer import JsonViewer
from flightpath.widgets.panels.csvpath_viewer import CsvpathViewer
from flightpath.widgets.panels.data_viewer import DataViewer
from flightpath.widgets.tabs_nonscrolling_tab_bar import NonScrollingTabBar
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
        self.setup_context_menu()
        #
        # exp
        #
        tab_bar = NonScrollingTabBar()
        self.setTabBar(tab_bar)

    def wheelEvent(self, event):
        event.ignore()

    def setup_context_menu(self) -> None:
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)

    def show_context_menu(self, pos):
        index = self.tabBar().tabAt(pos)
        if index == -1:
            return  # Clicked outside of any tab
        t = self.widget(index)
        #
        # this could allow for a ctx menu on the main tab bar if a file were named
        # "Matches". but that would be a weird name and a subtle impact. can probably just
        # ignore so we don't have to check what tab bar we are in.
        #
        if not t.objectName() == "Matches":
            return
        menu = QMenu(self)
        save_sample = QAction("Save sample", self)
        menu.addAction(save_sample)
        save_sample.triggered.connect(lambda: self.on_save_sample(index))
        menu.popup(self.mapToGlobal(pos))

    def on_save_sample(self, index:int) -> None:
        if index == -1:
            return  # Clicked outside of any tab
        #
        # find directory
        #
        path = self.main.selected_file_path
        print(f"tabs_cls: onsavesam: path 1: {path}")
        nos = Nos(path)
        if nos.isfile():
            path = os.path.dirname(path)
        t = self.widget(index)
        if not t.objectName() == "Matches":
            return
        l = t.layout()
        w = l.itemAt(0).widget()
        m = w.model()
        data = m.get_data()

        print(f"tabs_cls: onsavesam: path 2: {path}")
        self.main.save_sample(path=path, name="sample.csv", data=data)

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
        if self.parent and hasattr( self.parent, "do_i_close"):
            if not self.parent.do_i_close(t[0]):
                return False
        elif not self.main.content.do_i_close(t[0]):
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
        if self.parent.can_have_edit_tabs:
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
            if self.main.content == self.parent:
                self.main.selected_file_path = path
                self.main.statusBar().showMessage(f"  {path}")
                if isinstance(w, DataViewer):
                    self.main.content.toolbar.enable()
                else:
                    self.main.content.toolbar.disable()

