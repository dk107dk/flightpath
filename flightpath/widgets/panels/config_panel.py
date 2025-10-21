import os
import json
import sys
import traceback

from pathlib import Path
from PySide6.QtCore import Qt, QModelIndex
from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QStackedLayout,
    QApplication,
    QTreeWidget,
    QTreeWidgetItem,
    QListWidget,
    QListWidgetItem,
    QFormLayout
)

from flightpath.widgets.forms.blank_form import BlankForm
from flightpath.widgets.forms.server_form import ServerForm
from flightpath.widgets.forms.projects_form import ProjectsForm
from flightpath.widgets.forms.env_form import EnvForm
from flightpath.widgets.forms.cache_form import CacheForm
from flightpath.widgets.forms.config_form import ConfigForm
from flightpath.widgets.forms.extensions_form import ExtensionsForm
from flightpath.widgets.forms.errors_form import ErrorsForm
from flightpath.widgets.forms.inputs_form import InputsForm
from flightpath.widgets.forms.listeners_form import ListenersForm
from flightpath.widgets.forms.logging_form import LoggingForm
from flightpath.widgets.forms.results_form import ResultsForm
from flightpath.util.style_utils import StyleUtility as stut

from csvpath.util.config import Config


class ConfigPanel(QWidget):

    TREE_STYLE = """
            QTreeWidget {
                border: 1px solid #d0d0d0;
                margin: 0px;
                padding-left: 1px;
            }
            QTreeWidget::item:hover {
              color: #FFF;
              background: black;
            }
            QTreeWidget::item:selected {
              color: #FFF;
              background: gray;
            }
            """

    def __init__(self, main, filepath=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        #
        # we need the section names from config so we need a config.
        # this will need to be pointed at a config dir that is not
        # the processes starting cwd. we don't want people working
        # in the app's dir and we do want them creating as many separate
        # dev directories as needed.
        #
        # for now we'll just stick with local config/config.ini and
        # figure the rest out later.
        #
        self.config = main.csvpath_config
        self.main = main
        #
        # state is a json file called ./.state. it is just a ui state
        # persistence tool with some configuration.
        #
        self._sections = None
        self._configurables = None
        #
        # style stuff
        #
        self.setAttribute(Qt.WA_StyledBackground, True)
        stut.set_common_style(self)
        #
        # Sidebar menu
        self._tree = None
        #
        # set up the forms
        #
        self.forms_layout = QStackedLayout()
        self.forms = None
        #
        # what if we did setup forms only when the config first view?
        #
        #self.setup_forms()
        self.ready = False
        #
        #
        #
        self.h_layout = QHBoxLayout()
        self.layout = QVBoxLayout()
        self.h_layout.addWidget(self.tree)
        self.h_layout.addLayout(self.forms_layout)
        self.layout.addLayout(self.h_layout)
        self.setLayout(self.layout)
        self.title = QLabel("Configuration Settings")
        self.title.setStyleSheet("font-weight: bold;")

    def setup_forms(self, populate=True) -> None:
        print(f"config_panel: setup_forms starting")
        if self.forms and len(self.forms):
            #
            # clear the forms. this happens when the working dir changes.
            #
            for form in self.forms:
                self.forms_layout.removeWidget(form)
                form.deleteLater()

        print(f"config_panel: setup_forms: creating forms")
        self.forms = [
            BlankForm(main=self.main),
            ProjectsForm(main=self.main),
            EnvForm(main=self.main),
            CacheForm(main=self.main),
            ConfigForm(main=self.main),
            ErrorsForm(main=self.main),
            ExtensionsForm(main=self.main),
            InputsForm(main=self.main),
            ListenersForm(main=self.main),
            LoggingForm(main=self.main),
            ResultsForm(main=self.main),
            ServerForm(main=self.main)
        ]
        for form in self.forms:
            print(f"config_panel: setup_forms: adding form widget: {form}")
            self.forms_layout.addWidget(form)
            form.config = self.config
            if populate is True:
                form.populate()
        self.ready = True


    def populate_all_forms(self) -> None:
        print("config_panel: populate_all_forms starting")
        if self.ready is False or self.forms is None:
            print("config_panel: populate_all_forms: setting up forms")
            #
            # we ended up calling populate() twice on each form. for now we're just going to not do the work twice.
            # in a future refactor we can detangle this further.
            #
            self.setup_forms(populate=False)
        print("config_panel: populate_all_forms: iterating forms")
        for form in self.forms:
            print(f"config_panel: populate_all_forms: starting form: {form}")
            form.populate()
            print(f"config_panel: populate_all_forms: done with form: {form}")

    def switch_form(self, index:QModelIndex):
        form = index.data()
        parent = None
        fallback = f"config{os.sep}about.md"
        if index.parent():
            parent = index.parent().data()
        if form == "projects" or parent == "projects":
            self.main.config.show_help_for_form("projects", fallback=fallback)
            self.forms_layout.setCurrentIndex(1)
            self.title.setText("Projects")
        if form == "env" or parent == "env":
            self.main.config.show_help_for_form("env", fallback=fallback)
            self.forms_layout.setCurrentIndex(2)
            self.title.setText("Env")
        if form == "cache" or parent == "cache":
            self.main.config.show_help_for_form("cache", fallback=fallback)
            self.forms_layout.setCurrentIndex(3)
            self.title.setText("Cache")
        if form == "config" or parent == "config":
            self.main.config.show_help_for_form("config_path", fallback=fallback)
            self.forms_layout.setCurrentIndex(4)
            self.title.setText("Config file")
        elif form == "errors" or parent == "errors":
            self.main.config.show_help_for_form("errors", fallback=fallback)
            self.forms_layout.setCurrentIndex(5)
            self.title.setText("Errors")
        elif form == "extensions" or parent == "extensions":
            self.main.config.show_help_for_form("extensions", fallback=fallback)
            self.forms_layout.setCurrentIndex(6)
            self.title.setText("Extensions")
        elif form == "inputs" or parent == "inputs":
            self.main.config.show_help_for_form("inputs", fallback=fallback)
            self.forms_layout.setCurrentIndex(7)
            self.title.setText("Inputs")
        elif form in ["integrations", "listeners"] or parent in ["integrations", "listeners"]:
            self.main.config.show_help_for_form("listeners", fallback=fallback)
            self.forms_layout.setCurrentIndex(8)
            self.title.setText("Integrations")
            #self.title.setText("Listeners")
        elif form == "logging" or parent == "logging":
            self.main.config.show_help_for_form("logging", fallback=fallback)
            self.forms_layout.setCurrentIndex(9)
            self.title.setText("logging")
        elif form == "results" or parent == "results":
            self.main.config.show_help_for_form("results", fallback=fallback)
            self.forms_layout.setCurrentIndex(10)
            self.title.setText("results")
        elif form == "server" or parent == "server":
            self.main.config.show_help_for_form("server", fallback=fallback)
            self.forms_layout.setCurrentIndex(11)
            self.title.setText("server")

    @property
    def tree(self) -> QTreeWidget:
        if self._tree is None:
            tree = QTreeWidget()
            tree.setColumnCount(1)
            tree.setHeaderHidden(True)
            tree.setFixedWidth(180)
            tree.setIndentation(8)
            items = []
            for key, values in self.configurables.items():
                if key == "listeners":
                    key = "integrations"
                item = QTreeWidgetItem([key])

                for value in values:
                    child = QTreeWidgetItem([value])
                    item.addChild(child)
                items.append(item)
            tree.insertTopLevelItems(0, items)
            #tree.expandAll()
            tree.clicked.connect(self.switch_form)
            tree.setStyleSheet(ConfigPanel.TREE_STYLE)
            self._tree = tree
        return self._tree

    #
    # integrations have a panel that groups both their listener keys and
    # their own config section, if any. we keep the list in .state.
    #
    def is_integration(self, section) -> bool:
        integrations = self.main.state.data.get("integrations")
        return integrations and section in integrations

    #
    # everything not here is considered an "integration". (including
    # [scripts] and the storage backends; they are integrations too)
    #
    def is_core_section(self, section) -> bool:
        return section in self.core_sections

    @property
    def core_sections(self) -> list[str]:
        return [
            "config", "cache", "logging", "extensions", "errors", "functions", "results", "inputs", "listeners", "server"
        ]

    #
    # top sections are the sections in config.ini that are
    # not part of integrations. The integrations will be handled
    # differently
    #
    @property
    def top_config_sections(self) -> list[str]:
        if self._sections is None:
            self._sections = []
            self._sections.append("projects")
            self._sections.append("env")
            for s in self.core_sections:
            #for s in self.config._config.sections():
                if self.is_integration(s) or not self.is_core_section(s):
                    continue
                #
                # functions are not as easy to create these days. still doable
                # but not well documented. we don't need to call it out as a useful
                # thing for most people.
                #
                elif s == "functions":
                    continue
                if s == "csv_files" or s == "csvpath_files":
                    if "extensions" not in self._sections:
                        self._sections.append("extensions")
                    continue
                self._sections.append(s)
            self._sections.sort()
        return self._sections

    @property
    def configurables(self) -> dict[str,list[str]]:
        if self._configurables is None:
            self._configurables = {}
            for s in self.top_config_sections:
                items = []
                if s == "extensions":
                    items.append("csv_files")
                    items.append("csvpath_files")
                elif s in ["projects", "env"]:
                    items = []
                else:
                    pairs = []
                    try:
                        pairs = self.config._config.items(s)
                    except Exception:
                        ...
                    for pair in pairs:
                        #
                        # knock out keys that are likely to be distracting more than helpful
                        # for most users. anyone can edit the ini directly if they want these
                        # features.
                        #
                        if pair[0] == "on_unmatched_file_fingerprints":
                            continue
                        elif s == "listeners" and pair[0] != "groups":
                            continue
                        items.append(pair[0])
                items.sort()
                self._configurables[s] = items
        return self._configurables

    def save_all_forms(self) -> None: # , filepath: Path
        print(f"confpanel: save_all_forms: configpath: {self.config.configpath}, cwd: {self.main.state.cwd}")
        named_files = self.config.get(section="inputs", name="files")
        print(f"cfgpanel: save_all_forms: named_files: {named_files}")

        named_paths = self.config.get(section="inputs", name="csvpaths")
        archive = self.config.get(section="results", name="archive")
        #
        # TODO: using reload to assure config exists. if not a default
        # will be generated and loaded. which is fine because the forms
        # have all their changes still. in theory. this should change
        # in csvpath lib to better support the use case. :/
        #
        #
        # doing this at the initalization of the Config panel. if we have
        # a user editing config.ini and also at the same time using the UI
        # to edit config that's a level of unusual we can ignore.
        #
        # self.config.reload()
        #
        for form in self.forms:
            try:
                form.add_to_config(self.config) #self.metadata)
            except:
                print(traceback.format_exc())
        self.config.save_config()
        #
        # note that some non-config.ini values must/will be saved when add_to_config() is
        # called on their forms. e.g. projects.
        #

        #
        # need to refresh the inputs and results trees, but only
        # if the paths change
        #
        # TODO: or the extensions could have changed. check that too.
        #
        if named_files != self.config.get(section="inputs", name="files"):
            self.main.sidebar_rt_top.refresh()
        if named_paths != self.config.get(section="inputs", name="csvpaths"):
            self.main.sidebar_rt_mid.refresh()
        if archive != self.config.get(section="results", name="archive"):
            self.main.sidebar_rt_bottom.refresh()


