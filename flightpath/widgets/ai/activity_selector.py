from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QWidget, QHBoxLayout, QToolButton, QButtonGroup, QSizePolicy


class ActivitySelector(QWidget):
    activityChanged = Signal(str)

    ACTIVITIES = [
        ("validation", "📄", "Create"),
        ("question", "❓", "Ask"),
        ("improve", "🔧", "Improve"),
        ("testdata", "🧪", "Data"),
    ]



    def __init__(self, *, main, parent=None):
        super().__init__(parent)
        self.main = main
        self.setMinimumHeight(23)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.group = QButtonGroup(self)
        self.group.setExclusive(True)

        self.buttons = {}

        for key, icon, label in self.ACTIVITIES:
            btn = QToolButton(self)
            btn.setText(f"{icon}  {label}")
            btn.setCheckable(True)
            btn.setAutoExclusive(True)
            btn.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
            btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            btn.setFixedHeight(23)
            btn.setFixedWidth(74)
            layout.addWidget(btn)
            self.group.addButton(btn)
            self.buttons[key] = btn
        layout.addStretch(1)

        self.buttons["validation"].setChecked(True)

        self.group.buttonClicked.connect(self._on_clicked)




    def enable_for_extension(self, e:str, activity:str="validation") -> None:
        csv = [True,False,False,False]
        csvpath = [False,True,True,True]
        me = [
            self.buttons["validation"].isEnabled(),
            self.buttons["question"].isEnabled(),
            self.buttons["improve"].isEnabled(),
            self.buttons["testdata"].isEnabled()
        ]
        if e in self.main.csvpath_config.get(section="extensions", name="csv_files"):
            self.buttons["validation"].setEnabled(True)
            self.buttons["question"].setEnabled(False)
            self.buttons["improve"].setEnabled(False)
            self.buttons["testdata"].setEnabled(False)
            #
            # no testing for which activity should be checked=True because
            # there's only one option
            #
            self.buttons["validation"].setChecked(True)
            self.buttons["validation"].setChecked(False)
            self.buttons["question"].setChecked(False)
            self.buttons["improve"].setChecked(False)
        elif e in self.main.csvpath_config.get(section="extensions", name="csvpath_files"):
            if me != csvpath:
                self.buttons["question"].setChecked(True)
            self.buttons["validation"].setEnabled(False)
            self.buttons["question"].setEnabled(True)
            self.buttons["improve"].setEnabled(True)
            self.buttons["testdata"].setEnabled(True)
            #
            # which should be checked?
            #
            self.buttons["validation"].setChecked(activity == "valiation")
            self.buttons["question"].setChecked(activity == "question")
            self.buttons["improve"].setChecked(activity == "improve")
            self.buttons["testdata"].setChecked(False)
        else:
            #
            # any other file, e.g. a .md or .json
            #
            self.buttons["validation"].setChecked(False)
            self.buttons["question"].setChecked(False)
            self.buttons["improve"].setChecked(False)
            self.buttons["testdata"].setChecked(False)

            self.buttons["validation"].setEnabled(False)
            self.buttons["question"].setEnabled(False)
            self.buttons["improve"].setEnabled(False)
            self.buttons["testdata"].setEnabled(False)


    def _on_clicked(self, btn):
        for key, b in self.buttons.items():
            if b is btn:
                self.activityChanged.emit(key)
                break

    def set_activity(self, key: str):
        if key in self.buttons:
            self.buttons[key].setChecked(True)

