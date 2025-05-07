from PySide6.QtWidgets import QWidget, QTabWidget

class TabsUtility:

    @classmethod
    def find_tab(self, tabs, object_name) -> QWidget:
        for i in range(tabs.count()):
            widget = tabs.widget(i)
            if widget.objectName() == object_name:
                return (i, widget)
        return None

    @classmethod
    def has_type(self, tabs, cls) -> bool:
        for i in range(tabs.count()):
            widget = tabs.widget(i)
            if isinstance(widget, cls):
                return True
        return False

    @classmethod
    def select_tab(self, tabs:QTabWidget, i:int|QWidget) -> bool:
        if isinstance(i, int):
            if i >= tabs.count():
                raise ValueError("No such tab: {i}")
            tabs.setCurrentIndex(i)
            return True
        else:
            return TabsUtility.select_tab_widget(tabs, i)

    @classmethod
    def select_tab_widget(self, tabs:QTabWidget, w:QWidget) -> bool:
        t = TabsUtility.find_tab(tabs, w.objectName() )
        if t is None:
            return False
        tabs.setCurrentIndex(t[0])
        return True
