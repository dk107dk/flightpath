from PySide6.QtWidgets import (
    QLineEdit,
    QPushButton,
    QFormLayout,
    QVBoxLayout,
    QWidget,
    QSizePolicy,
)
from PySide6.QtCore import Qt
from .blank_form import BlankForm


class ExtensionsForm(BlankForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        #
        # =====================
        #
        overall = QVBoxLayout()
        overall.setContentsMargins(0, 0, 0, 0)
        form = QWidget()
        layout = QFormLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        form.setLayout(layout)

        self.csvs = QLineEdit()
        layout.addRow("Data file extensions: ", self.csvs)

        self.csvpaths = QLineEdit()
        layout.addRow("Csvpath file extensions: ", self.csvpaths)

        self.csvs.textChanged.connect(self._enable_reload)
        self.csvpaths.textChanged.connect(self._enable_reload)

        self.reload_button = QPushButton("Reload project files")
        self.reload_button.clicked.connect(self._refresh)
        layout.addRow("", self.reload_button)

        #
        # =====================
        #
        self.table.setContentsMargins(0, 0, 0, 0)
        self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.table.setMinimumHeight(
            self.table.verticalHeader().length()
            + self.table.horizontalHeader().height()
            + self.table.frameWidth() * 2
            + 4
        )
        overall.addWidget(form, 0)
        overall.addStretch(1)
        overall.addWidget(self.table, 0)
        overall.setAlignment(self.table, Qt.AlignBottom)
        self.setLayout(overall)
        self._setup()

    def _refresh(self) -> None:
        self.main.save_config_changes()
        self.main.sidebar._setup_tree(replace=True)
        #
        # the named-files could also change with the extensions, but not as likely.
        # the named-paths even less likely.
        #
        # self.main.sidebar._renew_sidebars()
        self.reload_button.setEnabled(False)

    def _enable_reload(self) -> None:
        self.reload_button.setEnabled(True)

    def add_to_config(self, config) -> None:
        config.add_to_config("extensions", "csv_files", self.csvs.text())
        #
        #
        #
        paths = self.csvpaths.text()
        config.add_to_config("extensions", "csvpath_files", paths)
        #
        #
        #

    def _setup(self) -> None:
        self.csvs.textChanged.connect(self.main.on_config_changed)
        self.csvpaths.textChanged.connect(self.main.on_config_changed)

    def populate(self):
        config = self.config
        csvs = config.get(
            section="extensions", name="csv_files", string_parse=False, swaps=False
        )
        self.csvs.setText(", ".join(csvs))
        csvpaths = config.get(
            section="extensions", name="csvpath_files", string_parse=False, swaps=False
        )
        self.csvpaths.setText(", ".join(csvpaths))

    @property
    def fields(self) -> list[str]:
        return ["csv_files", "csvpath_files"]

    @property
    def server_fields(self) -> list[str]:
        return self.fields

    @property
    def section(self) -> str:
        return "extensions"

    @property
    def tabs(self) -> list[str]:
        return []
