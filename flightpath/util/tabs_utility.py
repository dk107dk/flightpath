from PySide6.QtWidgets import QWidget, QTabWidget

class TabsUtility:

    @classmethod
    def find_tab(cls, tabs:QTabWidget, object_name) -> tuple[int,QWidget]:
        for i in range(tabs.count()):
            widget = tabs.widget(i)
            if widget.objectName() == object_name:
                return (i, widget)
        return None

    @classmethod
    def tab_index(cls, tabs:QTabWidget, tab:QWidget) -> int:
        i = cls.tab_index_if(tabs, tab)
        if i == -1:
            raise ValueError("No such tab")
        return i

    @classmethod
    def tab_index_if(cls, tabs:QTabWidget, tab:QWidget) -> int:
        for i in range(tabs.count()):
            widget = tabs.widget(i)
            if widget == tab:
                return i
        return -1


    @classmethod
    def tab_index_by_name(cls, tabs:QTabWidget, name:str) -> int:
        i = cls.tab_index_by_name_if(tabs, name)
        if i == -1:
            raise ValueError(f"No such tab: {name}")
        return i

    @classmethod
    def tab_index_by_name_if(cls, tabs:QTabWidget, name:str) -> int:
        for i in range(tabs.count()):
            widget = tabs.widget(i)
            if widget.objectName() == name:
                return i
        return -1




    @classmethod
    def tabs(cls, tabs:QTabWidget) -> list[QWidget]:
        ts = []
        for i in range(tabs.count()):
            widget = tabs.widget(i)
            ts.append(widget)
        return ts


    @classmethod
    def has_type(cls, tabs:QTabWidget, clsx) -> bool:
        for i in range(tabs.count()):
            widget = tabs.widget(i)
            if isinstance(widget, clsx):
                return True
        return False

    @classmethod
    def select_tab(cls, tabs:QTabWidget, i:int|QWidget) -> bool:
        if isinstance(i, int):
            if i >= tabs.count():
                raise ValueError("No such tab: {i}")
            tabs.setCurrentIndex(i)
            return True
        else:
            return TabsUtility.select_tab_widget(tabs, i)

    @classmethod
    def select_tab_widget(cls, tabs:QTabWidget, w:QWidget) -> bool:
        t = TabsUtility.find_tab(tabs, w.objectName() )
        if t is None:
            return False
        tabs.setCurrentIndex(t[0])
        return True
