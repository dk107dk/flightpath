from PySide6.QtWidgets import (
    QWidget,
    QLineEdit,
    QFormLayout,
    QComboBox,
    QHBoxLayout,
    QCheckBox
)

from csvpath.util.config import Config
from .blank_form import BlankForm

class ErrorsForm(BlankForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        layout = QFormLayout()

        self.pattern = QLineEdit()
        layout.addRow("Error pattern: ", self.pattern)

        self.use_format = QComboBox()
        layout.addRow("Error format: ", self.use_format)

        #
        # csvpath errors. checkboxes have to go into string but
        # will be much less error prone and pia
        #
        self.h_layout_csvpath = QHBoxLayout()
        self.csvpath_raise = QCheckBox("raise")
        self.h_layout_csvpath.addWidget(self.csvpath_raise)

        self.csvpath_print = QCheckBox("print")
        self.h_layout_csvpath.addWidget(self.csvpath_print)

        self.csvpath_stop = QCheckBox("stop")
        self.h_layout_csvpath.addWidget(self.csvpath_stop)

        self.csvpath_fail = QCheckBox("fail")
        self.h_layout_csvpath.addWidget(self.csvpath_fail)

        self.csvpath_collect = QCheckBox("collect")
        self.h_layout_csvpath.addWidget(self.csvpath_collect)

        layout.addRow("CsvPath errors: ", self.h_layout_csvpath)


        self.h_layout_csvpaths = QHBoxLayout()
        self.csvpaths_raise = QCheckBox("raise")
        self.h_layout_csvpaths.addWidget(self.csvpaths_raise)

        self.csvpaths_print = QCheckBox("print")
        self.h_layout_csvpaths.addWidget(self.csvpaths_print)

        self.csvpaths_stop = QCheckBox("stop")
        self.h_layout_csvpaths.addWidget(self.csvpaths_stop)

        self.csvpaths_fail = QCheckBox("fail")
        self.h_layout_csvpaths.addWidget(self.csvpaths_fail)

        self.csvpaths_collect = QCheckBox("collect")
        self.h_layout_csvpaths.addWidget(self.csvpaths_collect)

        layout.addRow("CsvPaths errors: ", self.h_layout_csvpaths)

        self.setLayout(layout)
        self._setup()

    def add_to_config(self, config) -> None:
        config.add_to_config("inputs", "pattern", self.pattern.text() )
        config.add_to_config("inputs", "use_format", self.use_format.currentText() )

        csvpath_policy = []
        if self.csvpath_raise.isChecked():
            csvpath_policy.append("raise")
        if self.csvpath_print.isChecked():
            csvpath_policy.append("print")
        if self.csvpath_stop.isChecked():
            csvpath_policy.append("stop")
        if self.csvpath_fail.isChecked():
            csvpath_policy.append("fail")
        if self.csvpath_collect.isChecked():
            csvpath_policy.append("collect")
        print(f"errorsform: add_to_config: csvpath_policy: {csvpath_policy}")
        config.csvpath_errors_policy = csvpath_policy

        csvpaths_policy = []
        if self.csvpaths_raise.isChecked():
            csvpaths_policy.append("raise")
        if self.csvpaths_print.isChecked():
            csvpaths_policy.append("print")
        if self.csvpaths_stop.isChecked():
            csvpaths_policy.append("stop")
        if self.csvpaths_fail.isChecked():
            csvpaths_policy.append("fail")
        if self.csvpaths_collect.isChecked():
            csvpaths_policy.append("collect")
        config.csvpaths_errors_policy = csvpaths_policy


    def _setup(self) -> None:
        self.use_format.activated.connect(self.main.on_config_changed)
        self.pattern.textChanged.connect(self.main.on_config_changed)

        self.csvpath_raise.stateChanged.connect(self.main.on_config_changed)
        self.csvpath_print.stateChanged.connect(self.main.on_config_changed)
        self.csvpath_stop.stateChanged.connect(self.main.on_config_changed)
        self.csvpath_fail.stateChanged.connect(self.main.on_config_changed)
        self.csvpath_collect.stateChanged.connect(self.main.on_config_changed)

        self.csvpaths_raise.stateChanged.connect(self.main.on_config_changed)
        self.csvpaths_print.stateChanged.connect(self.main.on_config_changed)
        self.csvpaths_stop.stateChanged.connect(self.main.on_config_changed)
        self.csvpaths_fail.stateChanged.connect(self.main.on_config_changed)
        self.csvpaths_collect.stateChanged.connect(self.main.on_config_changed)


    def populate(self):
        config = self.config
        pattern = config.get(section="errors", name="pattern")
        pattern = pattern if pattern else ""
        self.pattern.setText(pattern)

        self.use_format.clear()
        self.use_format.addItem("bare")
        self.use_format.addItem("full")
        use = config.get(section="errors", name="use_format", default="full")
        use = use.strip()
        if use == "bare":
            self.use_format.setCurrentText("bare")
        else:
            self.use_format.setCurrentText("full")

        csvpath_errors = config.get(section="errors", name="csvpath")
        if csvpath_errors is not None:
            self.csvpath_raise.setChecked("raise" in csvpath_errors)
            self.csvpath_print.setChecked("print" in csvpath_errors)
            self.csvpath_stop.setChecked("stop" in csvpath_errors)
            self.csvpath_fail.setChecked("fail" in csvpath_errors)
            self.csvpath_collect.setChecked("collect" in csvpath_errors)

        csvpaths_errors = config.get(section="errors", name="csvpaths")
        if csvpaths_errors is not None:
            self.csvpaths_raise.setChecked("raise" in csvpaths_errors)
            self.csvpaths_print.setChecked("print" in csvpaths_errors)
            self.csvpaths_stop.setChecked("stop" in csvpaths_errors)
            self.csvpaths_fail.setChecked("fail" in csvpaths_errors)
            self.csvpaths_collect.setChecked("collect" in csvpaths_errors)


