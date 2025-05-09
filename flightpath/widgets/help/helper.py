from PySide6.QtWidgets import QTextEdit
from PySide6.QtWidgets import QVBoxLayout
from PySide6.QtWidgets import QWidget

from flightpath.util.help_finder import HelpFinder
from flightpath.widgets.tabs_closing import ClosingTabs

class Helper:

    def __init__(self, main) -> None:
        self.main = main
        self._help = None
        self.help_and_feedback = None
        self.help_and_feedback_layout = None
        self.setup()

    def setup(self) -> None:
        if self.help_and_feedback:
            self.help_and_feedback.deleteLater()
            self.help_and_feedback = None
        self.help_and_feedback = ClosingTabs(main=self.main, parent=self)

    @property
    def help(self) -> QTextEdit:
        return self._help

    @help.setter
    def help(self, t:QTextEdit) -> None:
        self._help = t

    def assure_help_tab(self) -> None:
        if self.help is None:
            self.help = QTextEdit()
            self.help.setObjectName("Help Content")
        t = self.help_and_feedback.findChild(QWidget, "Help Content")
        if t is None:
            self.help_and_feedback.addTab(self.help, "Help Content")
        self.help_and_feedback.setCurrentWidget(t)
        self.help_and_feedback.show()

    def get_help_tab_if(self) -> QWidget:
        t = self.help_and_feedback.findChild(QWidget, "Help Content")
        return t

    def get_help_tab_index_if(self) -> int:
        for i in range(self.help_and_feedback.count()):
            if self.help_and_feedback.tabText(i) == "Help Content":
                return i
        return -1

    def get_help_tab(self) -> QWidget:
        i = self.get_help_tab_index_if()
        if i == -1:
            h = QTextEdit()
            h.setObjectName("Help Content")
            self.help_and_feedback.addTab(h, "Help Content")
            return h
        return self.help_and_feedback.widget(i)

    def on_click_help(self) -> None:
        if self.is_showing_help():
            self.close_help()
        else:
            self.open_help()

    def open_help(self) -> None:
        self.main.main.setSizes([1, 1])

    def close_help(self) -> None:
        self.main.main.setSizes([1, 0])

    def is_showing_help(self) -> bool:
        ss = self.main.main.sizes()
        if ss is None:
            return False
        if len(ss) <= 1:
            return False
        return ss[1] > 0

    def on_click_named_files_help(self) -> None:
        md = HelpFinder(main=self.main).help("named_files/about.md")
        self.get_help_tab().setMarkdown(md)
        if not self.is_showing_help():
            self.on_click_help()

    def on_click_named_paths_help(self) -> None:
        md = HelpFinder(main=self.main).help("named_paths/about.md")
        self.get_help_tab().setMarkdown(md)
        if not self.is_showing_help():
            self.on_click_help()

    def on_click_archive_help(self) -> None:
        md = HelpFinder(main=self.main).help("archive/about.md")
        self.get_help_tab().setMarkdown(md)
        if not self.is_showing_help():
            self.on_click_help()





