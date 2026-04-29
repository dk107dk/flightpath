import os
import json
import traceback
from typing import Callable

from PySide6.QtWidgets import (
    QTabWidget,
    QPushButton,
    QStyle,
    QTabBar,
    QMenu,
    QFileDialog,
    QTextEdit,
    QPlainTextEdit,
    QMessageBox,
    QWidget,
)
from PySide6.QtGui import QIcon, QAction, QPageLayout, QPageSize
from PySide6.QtPrintSupport import QPrinter
from PySide6.QtCore import Slot, Qt, QMarginsF

from csvpath.util.nos import Nos

from flightpath.widgets.panels.json_viewer import JsonViewer, KeyableTreeView
from flightpath.widgets.panels.csvpath_viewer import CsvpathViewer
from flightpath.widgets.panels.data_viewer import DataViewer
from flightpath.widgets.tabs_nonscrolling_tab_bar import NonScrollingTabBar
from flightpath.util.tabs_utility import TabsUtility as taut
from flightpath.util.message_utility import MessageUtility as meut


class ClosingTabs(QTabWidget):
    def __init__(self, *, main, parent=None):
        super().__init__(main)
        self.main = main
        #
        # if we live in content we (may) need to know it.
        # if we're the info & feedback we don't.
        #
        self.my_parent = parent
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

        # this could allow for a ctx menu on the main tab bar if a file were named
        # "Matches". but that would be a weird name and a subtle impact. can probably just
        # ignore so we don't have to check what tab bar we are in.
        #
        if t.objectName() in ["Code"]:
            return
        save_sample = None
        menu = QMenu(self)
        if t.objectName() in ["Why", "Help Content", "FileInfo"]:
            save_sample = QAction("Save to PDF", self)
            menu.addAction(save_sample)
            save_sample.triggered.connect(lambda: self.on_save_pdf(index))
            menu.popup(self.mapToGlobal(pos))
        else:
            save_sample = QAction("Save as", self)
            menu.addAction(save_sample)
            save_sample.triggered.connect(lambda: self.on_save_sample(index))
            menu.popup(self.mapToGlobal(pos))

    def on_save_pdf(self, index: int, landscape=False) -> None:
        t = self.widget(index)
        ton = t.objectName()
        if ton == "FileInfo":
            landscape = True
        path, _ = QFileDialog.getSaveFileName(
            self, "Export PDF", "", "PDF Files (*.pdf);;All Files (*)"
        )
        if path:
            if not path.lower().endswith(".pdf"):
                path += ".pdf"
            printer = QPrinter(QPrinter.HighResolution)
            printer.setOutputFormat(QPrinter.PdfFormat)

            margins = QMarginsF(0, 0, 0, 0)

            orientation = (
                QPageLayout.Orientation.Landscape
                if landscape is True
                else QPageLayout.Orientation.Portrait
            )
            layout = QPageLayout(QPageSize(QPageSize.A4), orientation, margins)
            layout.setMode(QPageLayout.FullPageMode)

            printer.setPageLayout(layout)
            printer.setPageMargins(margins)
            printer.setOutputFileName(path)

            document = None
            if isinstance(t, QTextEdit):
                document = t.document()
            else:
                item = t.layout().itemAt(0)
                document = item.widget().document()
            document.setTextWidth(600)

            document.print_(printer)

    def on_save_sample(self, index: int) -> None:
        if index == -1:
            return
        path = self.main.selected_file_path
        nos = Nos(path)
        if nos.isfile():
            path = os.path.dirname(path)
        t = self.widget(index)
        ton = t.objectName()
        if ton in ["Code", "Why", "Help Content"]:
            return
        if ton.startswith("Printouts"):
            ton = f"{ton}.txt"
            layout = t.layout()
            w = layout.itemAt(0).widget()
            txt = w.toPlainText()
            self.main.save_sample(path=path, name=ton, data=txt)
        elif ton == "Log":
            layout = t.layout()
            w = layout.itemAt(0).widget()
            txt = w.toPlainText()
            self.main.save_sample(path=path, name="run.log", data=txt)
        elif ton in ["Errors", "Variables"]:
            layout = t.layout()
            w = layout.itemAt(0).widget()
            #
            # exp
            #
            j = w.model.to_json()
            txt = json.dumps(j)
            self.main.save_sample(path=path, name=f"{ton}.json", data=txt)
        elif ton == "Matches":
            layout = t.layout()
            w = layout.itemAt(0).widget()
            m = w.model()
            data = m.get_data()
            self.main.save_sample(path=path, name="sample.csv", data=data)
        elif isinstance(t, QTextEdit):
            txt = t.toMarkdown()
            self.main.save_sample(path=path, name=ton, data=txt)
        elif isinstance(t, QPlainTextEdit):
            self.main.save_sample(
                path=path, name=f"{t.objectName()}.txt", data=t.toPlainText()
            )
        elif isinstance(t, DataViewer):
            path = t.path
            d = self.main.sidebar.selected_file_path()
            if d is None:
                d = self.main.state.cwd
            else:
                d = os.path.dirname(d)
            p = os.path.basename(path)
            path = os.path.join(d, p)
            t._save(path=path)
        elif isinstance(t, JsonViewer):
            self.main.save_sample(
                path=path, name=f"{t.objectName()}.json", data=t.to_json_str()
            )
        else:
            print("hitelse on saving")
            layout = t.layout()
            w = layout.itemAt(0).widget()
            if isinstance(w, KeyableTreeView):
                j = w.parent().model.to_json()
                self.main.save_sample(path=path, name=ton, data=j)
            else:
                txt = w.toPlainText()
                self.main.save_sample(path=path, name=ton, data=txt)

    @Slot(str)
    def close_tab(
        self, name: str, *, callback: Callable = None, args: dict = None
    ) -> None:
        #
        # we find tabs by name because the indexes change
        # using our own tab close icon made the changing
        # indexes difficult. and closing by file path is more
        # exact, anyway.
        #
        t = taut.find_tab(self, name)
        if t is None:
            raise ValueError(f"Tab named {name} cannot be None")

        i = taut.tab_index(self, t[1])
        self.setTabVisible(i, True)
        self.setCurrentIndex(i)
        #
        # we don't want to flip from config or welcome to content when a help tab is closed
        # so do we want this? not sure why it was here. or how it didn't screw things up
        # before.
        #
        # self.main.main_layout.setCurrentIndex(1)
        if not self.my_parent.modified(t[1]):
            self._close_tab_if(QMessageBox.Yes, t=t, callback=callback, args=args)
            return

        cn = (
            name[len(self.main.state.cwd) + 1 :]
            if name.startswith(self.main.state.cwd)
            else name
        )

        meut.yesNo2(
            parent=self,
            title="Close Without Saving?",
            msg=f"Close {cn} without saving?",
            callback=self._close_tab_if,
            args={"t": t, "callback": callback, "args": args},
        )

    @Slot(int)
    def _close_tab_if(
        self,
        answer: int,
        *,
        t: tuple[str, QWidget],
        callback: Callable = None,
        args: dict = None,
    ) -> None:
        if answer == QMessageBox.No:
            if callback:
                args = {} if args is None else args
                callback(**args)
            return
        if t is None:
            raise ValueError("No tab selected")
        try:
            self.removeTab(t[0])
            t[1].setParent(None)
            t[1].deleteLater()
            self._configure_tabs()
            if callback:
                args = {} if args is None else args
                callback(**args)
        except Exception:
            print(traceback.format_exc())

    def close_tab_at(self, index: int) -> bool:
        #
        # this is expected to be called where needed, e.g. content's
        # close all, but not connected for UI callbacks. see the comment
        # in close_tab above.
        #
        t = self.widget(index)
        if t:
            self.removeTab(index)
            t.setParent(None)
            t.deleteLater()
            self._configure_tabs()
            return True
        return False

    def _configure_tabs(self) -> None:
        #
        # show and hides
        #
        if self.my_parent.can_have_edit_tabs:
            if not self.has_data_tabs():
                self.main.reactor.on_data_toolbar_hide()
            if not self.has_csvpath_tabs():
                self.main.rt_tabs_hide()
        #
        # helper is responsable for the closing tabs it desplays help in
        # so we cannot use Helper directly. we could just assume any time
        # there is a parent we have a helper; checking the attr is probably
        # one better.
        #
        if self.count() == 0 and not hasattr(self.my_parent, "close_help"):
            self.main.main_layout.setCurrentIndex(0)
        elif self.count() == 0 and hasattr(self.my_parent, "close_help"):
            self.my_parent.close_help()
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
        close_button.setIcon(
            QIcon(self.style().standardIcon(QStyle.SP_TitleBarCloseButton))
        )
        close_button.setStyleSheet("border: none;")
        close_button.clicked.connect(lambda: self.close_tab(widget.objectName()))
        self.tabBar().setTabButton(index, QTabBar.ButtonPosition.LeftSide, close_button)

    def on_tab_change(self):
        i = self.currentIndex()
        w = self.widget(i)
        if w:
            path = w.objectName()
            if self.main.content == self.my_parent:
                self.main.selected_file_path = path
                self.main.statusBar().showMessage(f"  {path}")
                if isinstance(w, DataViewer):
                    self.main.content.toolbar.enable()
                else:
                    self.main.content.toolbar.disable()
