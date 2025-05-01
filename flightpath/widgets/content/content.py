
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QStackedLayout,
    QTabWidget,
    QTabBar
)

from flightpath.widgets.panels.data_viewer import DataViewer
from flightpath.widgets.panels.source_views.source import SourceViewer
from flightpath.widgets.panels.source_views.csvpath_source import CsvpathSourceViewer
from flightpath.widgets.panels.source_views.json_source import JsonSourceViewer

from flightpath.widgets.tab_overlay import TabWidgetOverlayButton


class Content(QWidget):

    def __init__(self, main):
        super().__init__()
        self.main = main
        layout = QVBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        self.csvpath_source_view = CsvpathSourceViewer(main=main)
        self.data_view = DataViewer(parent=self)
        self.source_view = SourceViewer(main=main)
        self.json_source_view = JsonSourceViewer(main=main)

        self.tab_widget = QTabWidget()
        self.tab_widget.addTab(self.data_view, "Grid Data View")
        self.tab_widget.addTab(self.source_view, "Source Data View")
        self.tab_widget.addTab(self.csvpath_source_view, "CsvPath Language")
        self.tab_widget.addTab(self.json_source_view, "JSON metadata")
        layout.setContentsMargins(1, 3, 1, 2)

        TabWidgetOverlayButton(self.tab_widget, main)

        layout.addWidget(self.tab_widget)
        self.setLayout(layout)

    def set_csvpath_tab_name(self, name:str) -> None:
        #
        # in principle this isn't needed because we open from the tree
        # and only have one doc open at once. in practice it's not
        # quite that simple. copying can make things unclear. and we
        # aren't good about moving the tree selection to match 100%.
        #
        # i like better w/o. at least till we need to have multiple docs
        # at the same time. we'll fix the stuff.
        #
        """
        t = self.tab_widget.widget(2)
        new_name = f"CsvPath Language: {name}"
        t.setObjectName(new_name)
        self.tab_widget.setTabText(2, new_name)
        """
