from PySide6.QtWidgets import QTabWidget, QPushButton, QStyle, QTabBar, QWidget
from PySide6.QtGui import QIcon
from PySide6.QtCore import Slot

class ClosingTabs(QTabWidget):
    def __init__(self, main):
        super().__init__()
        self.main = main
        #self.setTabsClosable(True)
        self.tabCloseRequested.connect(self.close_tab)
        self.index = {}

    @Slot(int)
    def close_tab(self, index):
        #print(f"closingtabs: close_tab: index of tab: {index}; index of tabs: {self.index}")
        title = self.index.get(index)
        if title is None:
            print(f"title of index: {index} is None in {self.index}")
        t = self.findChild(QWidget, title)
        i = self.indexOf(t)
        print(f"closingtabs: close_tab: i: {i}")
        self.removeTab(i)
        t.deleteLater()

        print(f"clear index: {index} from {self.index}")
        del self.index[index]

        #self.removeTab(index)
        if self.count() == 0:
            self.main.close_help()

    def addTab(self, widget, title):
        widget.setObjectName(title)
        index = super().addTab(widget, title)
        """
        pixmapi = QStyle.StandardPixmap.SP_TitleBarCloseButton
        icon = self.style().standardIcon(pixmapi)
        self.setTabIcon(index, icon)
        """

        #
        # exp. can we use a map to find the title given the original index
        # with the title find the current index...
        #
        print(f"add index: {index} into {self.index}")
        self.index[index] = title

        close_button = QPushButton()
        close_button.setIcon(QIcon(self.style().standardIcon(QStyle.SP_TitleBarCloseButton)))
        close_button.setStyleSheet("border: none;")
        #close_button.clicked.connect(self.close_tab)
        close_button.clicked.connect(lambda: self.close_tab(index))
        #print(f"closingtabs: addtab: index: {index}")
        self.tabBar().setTabButton(index, QTabBar.ButtonPosition.LeftSide, close_button)

