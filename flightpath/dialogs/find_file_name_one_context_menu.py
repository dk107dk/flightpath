from PySide6.QtWidgets import QLineEdit, QMenu
from PySide6.QtGui import QAction

class NameOneLineEdit(QLineEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main = parent.main
        self.parent = parent

    def contextMenuEvent(self, event):
        menu = QMenu()
        self._add_selectors_if(menu)
        self._add_tokens_if(menu)
        menu.exec(event.globalPos())

    def _add_selectors_if(self, menu) -> None:
        selectors_menu = QMenu("Selector", self)
        self._add_path_if(selectors_menu)
        self._add_date_if(selectors_menu)
        self._add_fingerprint_if(selectors_menu)
        self._add_instance_if(selectors_menu)
        if not selectors_menu.isEmpty():
            menu.addMenu(selectors_menu)

    def _add_fingerprint_if(self, menu) -> bool:
        if self.parent.datatype.currentText() == "files" and self.parent.name_one.text() == "":
            name = "Fingerprint"
            a = QAction(name, self)
            a.triggered.connect(lambda checked=False, name=name: self._on_add_to_ref(name))
            menu.addAction(a)

    def _add_date_if(self, menu) -> bool:
        s = self.parent.ref.sequence
        print(f"seq: {s}")
        if self.parent.name_one.text() == "":
            name = "yyyy-mm-dd_00-00-00"
            a = QAction(name, self)
            a.triggered.connect(lambda checked=False, name=name: self._on_add_to_ref(name))
            menu.addAction(a)

    def _add_path_if(self, menu) -> bool:
        s = self.parent.ref.sequence
        print(f"seq: {s}")
        if self.parent.name_one.text() == "":
            name = "relative/path"
            a = QAction(name, self)
            a.triggered.connect(lambda checked=False, name=name: self._on_add_to_ref(name))
            menu.addAction(a)

    def _add_instance_if(self, menu) -> bool:
        if self.parent.datatype.currentText() == "results" and self.parent.name_one.text() == "":
            name = "Csvpath name or ID"
            a = QAction(name, self)
            a.triggered.connect(lambda checked=False, name=name: self._on_add_to_ref(name))
            menu.addAction(a)

    def _add_tokens_if(self, menu) -> None:
        tokens_menu = QMenu("Limiters", self)
        self._add_ordinals_if(tokens_menu)
        self._add_ranges_if(tokens_menu)
        if not tokens_menu.isEmpty():
            menu.addMenu(tokens_menu)

    def _add_ranges_if(self, menu) -> None:
        ranges_menu = QMenu("Add a range", self)
        self._add_before_if(ranges_menu)
        self._add_to_if(ranges_menu)
        self._add_after_if(ranges_menu)
        self._add_from_if(ranges_menu)
        self._add_yesterday_if(ranges_menu)
        self._add_today_if(ranges_menu)
        self._add_all_if(ranges_menu)
        if not ranges_menu.isEmpty():
            menu.addMenu(ranges_menu)

    def _add_ordinals_if(self, menu) -> None:
        ordinals_menu = QMenu("Add an ordinal", self)
        self._add_first_if(ordinals_menu)
        self._add_last_if(ordinals_menu)
        self._add_index_if(ordinals_menu)
        if not ordinals_menu.isEmpty():
            menu.addMenu(ordinals_menu)

    #
    # ranges
    #

    def _add_before_if(self, menu) -> bool:
        for _ in self.parent.ref.next:
            if _.endswith("range"):
                self._add_range(":before", menu)

    def _add_to_if(self, menu) -> bool:
        for _ in self.parent.ref.next:
            if _.endswith("range"):
                self._add_range(":to", menu)

    def _add_after_if(self, menu) -> bool:
        for _ in self.parent.ref.next:
            if _.endswith("range"):
                self._add_range(":after", menu)

    def _add_from_if(self, menu) -> bool:
        for _ in self.parent.ref.next:
            if _.endswith("range"):
                self._add_range(":from", menu)

    def _add_yesterday_if(self, menu) -> bool:
        for _ in self.parent.ref.next:
            if _.endswith("range"):
                self._add_range(":yesterday", menu)

    def _add_today_if(self, menu) -> bool:
        for _ in self.parent.ref.next:
            if _.endswith("range"):
                self._add_range(":today", menu)

    def _add_all_if(self, menu) -> bool:
        for _ in self.parent.ref.next:
            if _.endswith("range"):
                self._add_range(":all", menu)

    def _add_range(self, name, menu):
        if self.parent.name_one.text().find(name) == -1:
            a = QAction(name, self)
            a.triggered.connect(lambda checked=False, name=name: self._on_add_to_ref(name))
            menu.addAction(a)

    #
    # ordinals
    #

    def _add_ordinal(self, name:str, menu) -> None:
        if self.parent.name_one.text().find(name) == -1:
            a = QAction(name, self)
            a.triggered.connect(lambda checked=False, name=name: self._on_add_to_ref(name))
            menu.addAction(a)

    def _add_first_if(self, menu) -> bool:
        for _ in self.parent.ref.next:
            if _.endswith("ordinal"):
                self._add_ordinal(":first", menu)

    def _add_last_if(self, menu) -> bool:
        for _ in self.parent.ref.next:
            if _.endswith("ordinal"):
                self._add_ordinal(":last", menu)

    def _add_index_if(self, menu) -> bool:
        return

    def _on_add_to_ref(self, name:str) -> None:
        t = self.parent.name_one.text()
        self.parent.name_one.setText(f"{t}{name}")


