import os
import traceback

from PySide6.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QMessageBox, QPlainTextEdit
from PySide6.QtCore import Qt, QFileInfo

from csvpath.util.file_readers import DataFileReader
from csvpath.util.file_writers import DataFileWriter

from flightpath.widgets.md_text_edit import MdTextEdit
from flightpath.widgets.raw_text_edit import RawTextEdit
from flightpath.util.printer import CapturePrinter
from flightpath.util.file_utility import FileUtility as fiut
from flightpath.util.log_utility import LogUtility as lout
from flightpath.util.file_collector import FileCollector
from flightpath.util.os_utility import OsUtility as osut
from flightpath.util.style_utils import StyleUtility as stut
from flightpath.util.message_utility import MessageUtility as meut

from flightpath.editable import EditStates

class MdViewer(QWidget):

    def __init__(self, *, main, editable=EditStates.EDITABLE, displaying:bool=True):
        super().__init__()
        self.main = main
        self.editable = editable
        #
        # set the font size
        #
        stut.set_common_style(self)
        #
        # displaying == MD
        # not displaying == editing == txt
        #
        self.displaying = displaying
        #
        #
        #
        layout = QVBoxLayout()
        self.setLayout(layout)
        self.saved = True
        self.path = None
        self.text_edit = None
        self._make_editor()
        layout.addWidget(self.text_edit)
        layout.setContentsMargins(0, 0, 0, 0)

    def _make_editor(self) -> None:
        if self.displaying is True:
            self.text_edit = MdTextEdit(main=self.main, parent=self, editable=self.editable)
        else:
            self.text_edit = RawTextEdit(main=self.main, parent=self, editable=self.editable)
        self.text_edit.setReadOnly(self.editable == EditStates.UNEDITABLE)
        #
        # remove widget
        #
        item = self.layout().itemAt(0)
        if item:
            #
            # we don't have to go to the layout if we remove before letting go of
            # self.text_edit. would that be better?
            #
            w = item.widget()
            w.setParent(None)
            w.deleteLater()
        #
        # add and show
        #
        self.layout().addWidget(self.text_edit)
        self.main.show_now_or_later(self.text_edit)
        #self.text_edit.show()

    def reset_saved(self) -> None:
        self.saved = True
        i = self.main.content.tab_widget.currentIndex()
        name = self.main.content.tab_widget.tabText(i)
        name = name.replace("+", "")
        self.main.content.tab_widget.setTabText(i, name )

    #
    # do we need this here?
    #
    def open_file(self, *, path:str, data:str) -> None:
        self.path = path
        info = QFileInfo(path)
        if not info.suffix() in ["md", "txt", "html"]:
            self.text_edit.hide()
            return
        self.text_edit.clear()
        #
        # internal operations can pass None in some cases. e.g. copying.
        #
        if data is None:
            with DataFileReader(path) as file:
                data = file.source.read()
        self.main.show_now_or_later(self.text_edit)
        if info.suffix() == "md":
            #
            # we can allow editing MD. need a raw view for that.
            #
            # QTextEdit does an ok job w/markdown but falls down on paragraph spacing
            # as a quick & effective fix we add \n<br/>\n when we see 2 whitespace lines
            #
            data = self._make_paragraphs(data)
            self.text_edit.setMarkdown(data)
            self.text_edit.display = "rich"

        elif info.suffix() == "html":
            #
            # we don't allow editing HTML
            #
            self.text_edit.setHtml(data)
            self.editable = EditStates.UNEDITABLE
            self.text_edit.setReadOnly(True)
            self.text_edit.display = "rich"
        elif info.suffix() == "txt":
            #
            # this is good as is. if editable editing works, ctrl-s, save( as) works.
            #
            self.text_edit.setText(data)
            self.text_edit.display = "plain"
        else:
            print(f"MdViewer: unknown file type: {info.suffix()}")
        c = "cmd" if osut.is_mac() else "ctrl"
        self.main.statusBar().showMessage(f"{c}-s to save • Opened {path}")
        self.main.show_now_or_later(self.text_edit)
        #self.text_edit.show()

    def clear(self):
        self.text_edit.hide()
        self.path = None

# =============================

    def on_save_as(self, switch_local=False) -> None:
        if self.editable == EditStates.UNEDITABLE:
            return
        thepath = self.text_edit.parent.path
        thepath = os.path.dirname(thepath)
        name = os.path.basename(self.path)

        name, ok = meut.input(title="Save As", msg="Where should the new file live? ")
        if ok and name:
            path = fiut.deconflicted_path( thepath, name )
            self._save(path=path)

    def _save(self, path:str) -> None:
        info = QFileInfo(self.path)
        txt = None
        if info.suffix() == "txt":
            txt = self.text_edit.toPlainText()
        elif info.suffix() == "md":
            #
            # markdown is well formed but it displays wrong unless we add
            # paragraph separators. we'll do that at load and toggle.
            #
            if self.displaying is True:
                txt = self.text_edit.toMarkdown()
            else:
                txt = self.text_edit.toPlainText()
        elif info.suffix() == "html":
            ... # error. html is not editable. if fix!
        with DataFileWriter(path=path) as writer:
            writer.write(txt)
        self.main.statusBar().showMessage(f"  Saved to: {path}")
        self.reset_saved()

    def on_save(self) -> None:
        if self.editable == EditStates.UNEDITABLE:
            return
        self._save(path=self.path)

    def on_toggle(self) -> None:
        info = QFileInfo(self.path)
        if info.suffix() in ["md"]:
        #if info.suffix() in ["md", "txt"]:
            editor = self.text_edit
            if self.displaying is True:
                self.displaying = False
                txt = editor.toMarkdown()
                self._make_editor()
                self.text_edit.setPlainText(txt)
            else:
                self.displaying = True
                editor = self.text_edit
                txt = editor.toPlainText()
                self._make_editor()
                txt = self._make_paragraphs(txt)
                self.text_edit.setMarkdown(txt)
            editor.hide()
            editor.deleteLater()
        else:
            print(f"md_viewer: cannot toggle {info}")

    def _make_paragraphs(self, txt:str) -> str:
        ss = txt.split("\n")
        ntxt = []
        last = False
        for i, s in enumerate(ss):
            if s.strip() == "" and not last:
                # make a para break
                # must be \n<br/>\n
                ntxt.append("\n")
                ntxt.append("<br/>")
                ntxt.append("\n")
                last = True
            else:
                ntxt.append(s)
                last = False
        return "\n".join(ntxt)

