from PySide6.QtWidgets import (
    QWidget,
    QLineEdit,
    QFormLayout,
    QComboBox,
    QLabel
)

from csvpath.util.config import Config
from .blank_form import BlankForm

class LlmForm(BlankForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        layout = QFormLayout()
        self.model = QLineEdit()
        layout.addRow(f"Model: ", self.model)

        self.base = QLineEdit()
        layout.addRow("API base: ", self.base)

        self.key = QLineEdit()
        layout.addRow("API key: ", self.key)

        self.setLayout(layout)
        self._setup()

    def _setup(self) -> None:
        self.model.textChanged.connect(self.main.on_config_changed)
        self.base.textChanged.connect(self.main.on_config_changed)
        self.key.textChanged.connect(self.main.on_config_changed)

    def add_to_config(self, config) -> None:
        config.add_to_config("llm", "model", self.model.text() )
        config.add_to_config("llm", "api_base", self.base.text() )
        config.add_to_config("llm", "api_key", self.key.text() )

    def populate(self):
        config = self.config
        _ = config.get(section="llm", name="model")
        self.model.setText(_)
        _ = config.get(section="llm", name="api_base")
        self.base.setText(_)
        _ = config.get(section="llm", name="api_key")
        self.key.setText(_)

    @property
    def fields(self) -> list[str]:
        return ["model", "api_base", "api_key"]

    @property
    def server_fields(self) -> list[str]:
        return self.fields

    @property
    def section(self) -> str:
        return "llm"

    @property
    def tabs(self) -> list[str]:
        return []

