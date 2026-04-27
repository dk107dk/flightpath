from typing import Callable

from PySide6.QtWidgets import QVBoxLayout, QToolBar

from flightpath.widgets.panels.csvpath_viewer import CsvpathViewer
from flightpath.widgets.panels.json_viewer_2 import JsonViewer2
from flightpath.widgets.panels.json_viewer import JsonViewer
from flightpath.widgets.panels.data_viewer import DataViewer
from flightpath.widgets.panels.md_viewer import MdViewer
from flightpath.widgets.tab_overlay import TabWidgetOverlayButton
from flightpath.widgets.tabs_closing import ClosingTabs
from flightpath.widgets.tabs_closing_holder import ClosingTabsHolder
from flightpath.widgets.toolbars.data_toolbar import DataToolbar
from flightpath.util.editable import EditStates


class Content(ClosingTabsHolder):
    def __init__(self, main):
        super().__init__(parent=main, can_have_edit_tabs=True)
        self.main = main
        layout = QVBoxLayout()
        layout.setSpacing(0)
        # we reset the margins below. is there a reason to do it here too?
        layout.setContentsMargins(0, 0, 0, 0)

        self.tab_widget = ClosingTabs(main=main, parent=self)
        TabWidgetOverlayButton(self.tab_widget, self, main)
        layout.addWidget(self.tab_widget)
        layout.setContentsMargins(1, 3, 1, 2)
        self.setLayout(layout)
        self._do_i_close_reentry_block = False

        ts = self.main.findChildren(QToolBar)
        if len(ts) == 0:
            self.toolbar = DataToolbar(parent=self, main=self.main)
        elif len(ts) > 1:
            raise RuntimeError("Cannot have {len(ts)} toolbar instances")
        else:
            self.toolbar = ts[0]
            self.toolbar.parent = self

    def csvpath_files_are_saved(self) -> bool:
        for i in range(self.tab_widget.count()):
            widget = self.tab_widget.widget(i)
            if isinstance(widget, CsvpathViewer) and not widget.saved:
                return False
        return True

    def json_files_are_saved(self) -> bool:
        for i in range(self.tab_widget.count()):
            widget = self.tab_widget.widget(i)
            if isinstance(widget, (JsonViewer2, JsonViewer)) and widget.modified:
                return False
        return True

    def data_files_are_saved(self) -> bool:
        for i in range(self.tab_widget.count()):
            widget = self.tab_widget.widget(i)
            if isinstance(widget, DataViewer):
                #
                # if it is not an editable file we skip ahead as if it were saved, regardless
                #
                if widget.editable == EditStates.UNEDITABLE:
                    continue
                if widget.saved is True:
                    continue
                return False
        return True

    def all_files_are_saved(self) -> bool:
        for i in range(self.tab_widget.count()):
            widget = self.tab_widget.widget(i)
            m = self.modified(widget)
            if m is True:
                return False
        return True

    def modified(self, widget) -> bool:
        cmod = isinstance(widget, CsvpathViewer) and not widget.saved
        jmod2 = isinstance(widget, JsonViewer2) and widget.modified
        jmod = isinstance(widget, JsonViewer) and widget.modified
        mmod = isinstance(widget, MdViewer) and not widget.saved
        dmod = isinstance(widget, DataViewer) and not widget.saved
        mod = cmod or jmod or jmod2 or mmod or dmod
        return mod

    def close_all_tabs(self, *, callback: Callable = None, args: dict = None):
        close = []
        for i in range(self.tab_widget.count()):
            close.append(self.tab_widget.widget(i))
        for widget in close:
            self.tab_widget.close_tab(widget.objectName(), callback=callback, args=args)
