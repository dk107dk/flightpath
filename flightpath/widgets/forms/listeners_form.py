from PySide6.QtWidgets import (
    QWidget,
    QLineEdit,
    QLabel,
    QFormLayout,
    QTabWidget,
    QHBoxLayout,
    QVBoxLayout,
    QScrollArea
)
from PySide6.QtCore import Qt, Slot
from csvpath.util.config import Config
from flightpath.widgets.clickable_label import ClickableLabel
from .blank_form import BlankForm
from .tabs.ckan_tab import CkanTab
from .tabs.otlp_tab import OtlpTab
from .tabs.sql_tab import SqlTab
from .tabs.marquez_tab import MarquezTab
from .tabs.scripts_tab import ScriptsTab
from .tabs.sftp_tab import SftpTab
from .tabs.sftpplus_tab import SftpPlusTab
from .tabs.slack_tab import SlackTab
from .tabs.sqlite_tab import SqliteTab


class ListenersForm(BlankForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.area = None
        self.area_box = None
        self._group_tabs = None
        self._setup_area()
        self._setup_tabs()
        layout = QFormLayout()
        self.groups = QLineEdit()
        layout.addRow("Active listener groups: ", self.groups)
        layout.addRow(self.area_box)
        layout.addRow(self.my_tabs)
        self.setLayout(layout)
        self._setup()

    def add_to_config(self, config) -> None:
        config.add_to_config("listeners", "groups", self.groups.text() )
        #
        #
        #
        for k, v in self._group_tabs.items():
            if v is None:
                continue
            v.add_to_config(config)

    def _setup(self) -> None:
        self.groups.textChanged.connect(self.main.on_config_changed)

    def populate(self):
        config = self.config
        nf = config.get(section="listeners", name="groups")
        if isinstance(nf, list):
            self.groups.setText(",".join(nf) )
        else:
            self.groups.setText(nf)
        #for k, v in self._group_tabs.items():
        for i, k in enumerate(self._group_tabs):
            #
            # should we disable tabs of integrations that haven't been selected?
            #
            v = self._group_tabs.get(k)
            if v is None:
                continue
            v.populate()

    @property
    def group_names(self) -> list[str]:
        if self._group_tabs is None:
            groups = {}
            groups["ckan"] = CkanTab(form=self)
            groups["default"] = None
            groups["openlineage"] = MarquezTab(form=self)
            groups["otlp"] = OtlpTab(form=self)
            groups["scripts"] = ScriptsTab(form=self)
            groups["sftp"] = SftpTab(form=self)
            groups["sftpplus"] = SftpPlusTab(form=self)
            groups["slack"] = SlackTab(form=self)
            groups["sql"] = SqlTab(form=self)
            groups["sqlite"] = SqliteTab(form=self)
            groups["webhook"] = None
            self._group_tabs = groups
        return self._group_tabs.keys()

    @property
    def tab_groups(self) -> dict[str,QWidget]:
        if self.group_names is None:
            ... # will never be None just because we check
        return self._group_tabs

    def _setup_tabs(self) -> None:
        self.my_tabs = QTabWidget()
        self.my_tabs.setFixedHeight(420)

        groups = self.group_names
        for group in groups:
            t = self.tab_groups.get(group)
            if t is None:
                continue
            self.my_tabs.addTab(t, group)

    def _setup_area(self) -> None:
        self.area = QScrollArea()
        self.area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.area.setWidgetResizable(False)
        self.area.setFixedHeight(90)
        self.area.setFixedWidth(340)
        self.area.setStyleSheet("QScrollArea {padding:3px 0 0 0;border:0}")
        self.area.horizontalScrollBar().setStyleSheet("QScrollBar {height: 0px;}")
        #
        #
        #
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.area.setLayout(layout)

        groups = self.group_names
        h = QWidget()
        hlayout = QHBoxLayout()
        hlayout.setContentsMargins(0, 0, 0, 0)
        hlayout.setSpacing(0)
        h.setLayout(hlayout)
        layout.addWidget(h)
        for i, group in enumerate(groups):
            if i > 0 and i % 5 == 0:
                h = QWidget()
                hlayout = QHBoxLayout()
                hlayout.setContentsMargins(0, 0, 0, 0)
                hlayout.setSpacing(0)
                h.setLayout(hlayout)
                layout.addWidget(h)
            if i % 5 != 0:
                s = QLabel()
                s.setText(" | ")
                s.setAlignment(Qt.AlignCenter)
                s.adjustSize()
                hlayout.addWidget(s)
            p = ClickableLabel()
            p.setText(group)
            p.setAlignment(Qt.AlignCenter)
            p.clicked.connect(self._listener_name_click)
            p.setStyleSheet("QLabel {color:#885522;}")
            p.adjustSize()
            hlayout.addWidget(p)
            if i == len(groups) - 1:
                while i % 5 != 0:
                    s = QLabel()
                    s.setText(f"      ")
                    s.setAlignment(Qt.AlignCenter)
                    s.adjustSize()
                    hlayout.addWidget(s)
                    i += 1

        self.area_box = QWidget()
        self.area_box.setStyleSheet("QWidget {border:0}")
        area_box_layout = QHBoxLayout()
        self.area_box.setLayout(area_box_layout)
        area_box_layout.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignTop)
        area_box_layout.addWidget(self.area)


    @Slot(str)
    def _listener_name_click(self, text:str) -> None:
        t = self.groups.text()
        if t is None:
            t = text
        ts = [ t.strip() for t in t.split("|")]

        if text in ts:
            return

        c = ', ' if t != '' else ''
        nt = f"{t}{c}{text}"
        self.groups.setText( nt )


    @property
    def fields(self) -> list[str]:
        return ["groups"]

    @property
    def server_fields(self) -> list[str]:
        return ["groups"]

    @property
    def section(self) -> str:
        return "listeners"

    @property
    def tabs(self) -> list[str]:
        print(f"tasxt:: {self._group_tabs}")
        return self._group_tabs.values()


