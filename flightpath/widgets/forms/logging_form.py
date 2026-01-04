from PySide6.QtWidgets import (
    QWidget,
    QLineEdit,
    QFormLayout,
    QComboBox
)

from csvpath.util.config import Config
from .blank_form import BlankForm

class LoggingForm(BlankForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        layout = QFormLayout()

        self.handler = QComboBox()
        layout.addRow("Handler type: ", self.handler)

        self.path = QLineEdit()
        layout.addRow("Log file path: ", self.path)

        self.log_files_to_keep = QLineEdit()
        layout.addRow("Number of log files to keep: ", self.log_files_to_keep)

        self.log_file_size = QLineEdit()
        layout.addRow("Max log file size: ", self.log_file_size)

        self.csvpath_level = QComboBox()
        layout.addRow("CsvPath log level: ", self.csvpath_level)

        self.csvpaths_level = QComboBox()
        layout.addRow("CsvPaths log level: ", self.csvpaths_level)

        self.setLayout(layout)
        self._setup()

    def add_to_config(self, config) -> None:
        config.add_to_config("logging", "handler", self.handler.currentText() )
        config.add_to_config("logging", "log_file_size", self.log_file_size.text() )
        config.add_to_config("logging", "log_files_to_keep", self.log_files_to_keep.text() )
        config.add_to_config("logging", "log_file", self.path.text() )
        config.add_to_config("logging", "csvpath", self.csvpath_level.currentText() )
        config.add_to_config("logging", "csvpaths", self.csvpaths_level.currentText() )



    def _setup(self) -> None:
        self.path.textChanged.connect(self.main.on_config_changed)
        self.log_files_to_keep.textChanged.connect(self.main.on_config_changed)
        self.log_file_size.textChanged.connect(self.main.on_config_changed)
        self.handler.activated.connect(self.main.on_config_changed)
        self.csvpath_level.activated.connect(self.main.on_config_changed)
        self.csvpaths_level.activated.connect(self.main.on_config_changed)

    def populate(self):
        config = self.config
        path = config.get(section="logging", name="log_file", default="logs/csvpath.log")
        self.path.setText(path)
        log_files_to_keep = config.get(section="logging", name="log_files_to_keep", default="10")
        self.log_files_to_keep.setText(str(log_files_to_keep))
        log_file_size = config.get(section="logging", name="log_file_size", default="50000000")
        self.log_file_size.setText(str(log_file_size))

        self.handler.clear()
        self.handler.addItem("file")
        self.handler.addItem("rotating")
        handler = config.get(section="logging", name="handler", default="file")
        handler = handler.strip()
        if handler == "file":
            self.handler.setCurrentText("file")
        if handler == "rotating":
            self.handler.setCurrentText("rotating")

        self.csvpath_level.clear()
        self.csvpath_level.addItem("debug")
        self.csvpath_level.addItem("info")
        self.csvpath_level.addItem("warn")
        self.csvpath_level.addItem("error")
        level = config.get(section="logging", name="csvpath", default="info")
        level = level.strip()
        if level == "debug":
            self.csvpath_level.setCurrentText("debug")
        elif level == "info":
            self.csvpath_level.setCurrentText("info")
        elif level == "warn":
            self.csvpath_level.setCurrentText("warn")
        else:
            self.csvpath_level.setCurrentText("error")

        self.csvpaths_level.clear()
        self.csvpaths_level.addItem("debug")
        self.csvpaths_level.addItem("info")
        self.csvpaths_level.addItem("warn")
        self.csvpaths_level.addItem("error")
        level = config.get(section="logging", name="csvpaths", default="info")
        level = level.strip()
        if level == "debug":
            self.csvpaths_level.setCurrentText("debug")
        elif level == "info":
            self.csvpaths_level.setCurrentText("info")
        elif level == "warn":
            self.csvpaths_level.setCurrentText("warn")
        else:
            self.csvpaths_level.setCurrentText("error")


    @property
    def fields(self) -> list[str]:
        return ["handler","log_file_size","log_files_to_keep","log_file","csvpath","csvpaths"]

    @property
    def server_fields(self) -> list[str]:
        return ["handler","log_file_size","log_files_to_keep","csvpath","csvpaths"]

    @property
    def section(self) -> str:
        return "logging"

    @property
    def tabs(self) -> list[str]:
        return []


