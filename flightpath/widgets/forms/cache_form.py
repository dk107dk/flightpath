from PySide6.QtWidgets import (
    QWidget,
    QLineEdit,
    QFormLayout,
    QComboBox,
    QLabel
)

from csvpath.util.config import Config
from .blank_form import BlankForm

class CacheForm(BlankForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        layout = QFormLayout()

        self.use_cache = QComboBox()
        layout.addRow("Use cache: ", self.use_cache)

        self.cache_dir_path = QLineEdit()
        layout.addRow("Cache directory: ", self.cache_dir_path)
        msg = QLabel("The default is cache.")
        msg.setStyleSheet("QLabel { font-size: 12pt; font-style:italic;color:#222222;}")
        layout.addRow("", msg)

        self.setLayout(layout)
        self._setup()

    def _setup(self) -> None:
        self.use_cache.activated.connect(self.main.on_config_changed)
        self.cache_dir_path.textChanged.connect(self.main.on_config_changed)

    def add_to_config(self, config) -> None:
        path = self.cache_dir_path.text()
        usecache = self.use_cache.currentText()
        config.add_to_config("cache", "path", path )
        config.add_to_config("cache", "use_cache", usecache)

    def populate(self):
        config = self.config
        cache_path = config.get(section="cache", name="path", default="cache")
        self.cache_dir_path.setText(cache_path)
        self.use_cache.clear()
        self.use_cache.addItem("yes")
        self.use_cache.addItem("no")
        use = config.get(section="cache", name="use_cache", default="yes")
        use = use.strip().lower()
        #
        # no is correct, but we'll take false because it's a reasonable guess.
        # everything else indicates yes.
        #
        if use in ["no", "false"]:
            self.use_cache.setCurrentText("no")
        else:
            self.use_cache.setCurrentText("yes")



