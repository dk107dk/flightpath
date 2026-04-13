from PySide6.QtWidgets import (
    QWidget,
    QLineEdit,
    QFormLayout,
    QPushButton,
    QHBoxLayout,
    QLabel,
)

from csvpath.util.date_util import DateUtility as daut
from .blank_form import BlankForm


class OffsetsForm(BlankForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.original_projects_home = None

        layout = QFormLayout()
        self.days = QLineEdit()
        self.months = QLineEdit()
        self.years = QLineEdit()
        self.now = QLabel(str(daut.now()))
        layout.addRow("Days: ", self.days)
        layout.addRow("Months: ", self.months)
        layout.addRow("Years: ", self.years)
        layout.addRow("Now: ", self.now)
        setbutton = QPushButton("Set date offsets")
        resetbutton = QPushButton("Reset")

        buttons = QWidget()
        blayout = QHBoxLayout()
        buttons.setLayout(blayout)
        setbutton.clicked.connect(self.on_set)
        blayout.addWidget(setbutton)

        resetbutton.clicked.connect(self.on_reset)
        blayout.addWidget(resetbutton)

        layout.addRow("", buttons)

        self.setLayout(layout)
        self.setup()

    def setup(self) -> None:
        di = daut.OFFSET_DAYS if isinstance(daut.OFFSET_DAYS, int) else 0
        mi = daut.OFFSET_MONTHS if isinstance(daut.OFFSET_MONTHS, int) else 0
        yi = daut.OFFSET_YEARS if isinstance(daut.OFFSET_YEARS, int) else 0

        self.days.setText(str(di))
        self.months.setText(str(mi))
        self.years.setText(str(yi))

    def on_reset(self) -> None:
        daut.OFFSET_DAYS = 0
        daut.OFFSET_MONTHS = 0
        daut.OFFSET_YEARS = 0

    def on_set(self) -> None:
        d = self.days.text()
        m = self.months.text()
        y = self.years.text()
        di = mi = yi = 0

        try:
            di = int(d)
        except (TypeError, ValueError):
            self.days.setText("")

        try:
            mi = int(m)
        except (TypeError, ValueError):
            self.months.setText("")

        try:
            yi = int(y)
        except (TypeError, ValueError):
            self.years.setText("")

        daut.OFFSET_DAYS = di
        daut.OFFSET_MONTHS = mi
        daut.OFFSET_YEARS = yi
        self.now.setText(str(daut.now()))
        # print(f"setting now: daut.now: {daut.now()}")

    def add_to_config(self, config) -> None: ...

    #
    # we only make a change from clicking the button on this form.
    # anything else is more likely to be disruptive.
    #
    def populate(self): ...

    @property
    def fields(self) -> list[str]:
        return []

    @property
    def server_fields(self) -> list[str]:
        return []

    @property
    def section(self) -> str:
        return "offsets"

    @property
    def tabs(self) -> list[str]:
        return []
