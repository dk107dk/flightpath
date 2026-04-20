from PySide6.QtWidgets import (
    QLineEdit,
    QFormLayout,
    QComboBox,
    QLabel,
    QVBoxLayout,
    QWidget,
    QSizePolicy,
)
from PySide6.QtCore import Qt

from .blank_form import BlankForm

"""
class PLineEdit(QLineEdit):
    def setText(self, t: str) -> None:
        pass
"""


class CacheForm(BlankForm):
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

        self.use_cache = QComboBox()
        layout.addRow("Use cache: ", self.use_cache)
        self._cache_dir_path = QLineEdit()
        layout.addRow("Cache directory: ", self._cache_dir_path)
        msg = QLabel("The default is cache.")
        msg.setStyleSheet("QLabel { font-size: 12pt; font-style:italic;color:#222222;}")
        layout.addRow("", msg)

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

    @property
    def cache_dir_path(self) -> QLineEdit:
        return self._cache_dir_path

    def _setup(self) -> None:
        self.use_cache.activated.connect(self.main.on_config_changed)
        self.cache_dir_path.textChanged.connect(self.main.on_config_changed)

    def add_to_config(self, config) -> None:
        path = self.cache_dir_path.text()
        usecache = self.use_cache.currentText()
        config.add_to_config("cache", "path", path)
        config.add_to_config("cache", "use_cache", usecache)

    def populate(self):
        if self.is_populating:
            return
        else:
            self.is_popualting = True
            config = self.config
            cache_path = config.get(
                section="cache",
                name="path",
                default="cache",
                string_parse=False,
                swaps=False,
            )
            self.cache_dir_path.setText(cache_path)

            self.use_cache.clear()
            self.use_cache.addItem("yes")
            self.use_cache.addItem("no")
            use = config.get(
                section="cache", name="use_cache", default="yes", swaps=False
            )
            use = use.strip().lower()
            #
            # no is correct, but we'll take false because it's a reasonable guess.
            # everything else indicates yes.
            #
            if use in ["no", "false"]:
                self.use_cache.setCurrentText("no")
            else:
                self.use_cache.setCurrentText("yes")
            self.is_populating = False

    @property
    def fields(self) -> list[str]:
        return ["path", "use_cache"]

    @property
    def server_fields(self) -> list[str]:
        return []

    @property
    def section(self) -> str:
        return "cache"

    @property
    def tabs(self) -> list[str]:
        return []
