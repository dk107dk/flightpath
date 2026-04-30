from pathlib import Path
import os

import darkdetect

from PySide6.QtWidgets import (  # pylint: disable=E0611
    QWidget,
    QVBoxLayout,
    QFileDialog,
    QMessageBox,
    QTextEdit,
)
from PySide6.QtCore import (  # pylint: disable=E0611
    QFileInfo,
    Slot,
    QModelIndex,
    QCoreApplication,
)

from csvpath.util.nos import Nos

from flightpath.widgets.panels.json_viewer_2 import JsonViewer2
from flightpath.widgets.sidebars.sidebar_functions import SidebarFunctions
from flightpath.widgets.sidebars.sidebar_docs import SidebarDocs
from flightpath.widgets.ai.query_tab import QueryTabWidget

from flightpath.util.file_utility import FileUtility as fiut
from flightpath.util.tabs_utility import TabsUtility as taut
from flightpath.util.message_utility import MessageUtility as meut
from flightpath.util.style_utils import StyleUtility as stut
from flightpath.util.html_generator import HtmlGenerator
from flightpath.util.editable import EditStates

from flightpath.inspect.inspector import Inspector


class Reactor:
    def __init__(self, main):
        self.main = main

    def on_rt_tree_click(self):
        nos = Nos(self.main.selected_file_path)
        if nos.isfile():
            ed = (
                EditStates.EDITABLE
                if self.main.selected_file_path.endswith(".md")
                else EditStates.UNEDITABLE
            )
            self.main.read_validate_and_display_file(editable=ed)
            self.main.statusBar().showMessage(f"  {self.main.selected_file_path}")

    def on_archive_tree_click(self, index):
        self.main.selected_file_path = self.main.sidebar_rt_bottom.model.filePath(index)
        self.on_rt_tree_click()

    def on_named_file_tree_click(self, index):
        self.main.selected_file_path = self.main.sidebar_rt_top.model.filePath(index)
        self.on_rt_tree_click()

    def on_named_paths_tree_click(self, index):
        self.main.selected_file_path = self.main.sidebar_rt_mid.model.filePath(index)
        self.on_rt_tree_click()

    def on_color_scheme_changed(self) -> None:
        QCoreApplication.instance().setStyle("Fusion")
        #
        # splitters apparently need special handling.
        #
        if darkdetect.isDark():
            s = "QSplitter::handle { background-color: #535353;  margin:1px; }"
            self.main.centralWidget().setStyleSheet(s)
            if self.main.rt_col_helpers:
                self.main.rt_col_helpers.setStyleSheet(s)
            if self.main.rt_col:
                self.main.rt_col.setStyleSheet(s)
            self.main.main.setStyleSheet(s)
        if darkdetect.isLight():
            s = "QSplitter::handle { background-color: #f3f3f3;  margin:1px; }"
            self.main.centralWidget().setStyleSheet(s)
            if self.main.rt_col_helpers:
                self.main.rt_col_helpers.setStyleSheet(s)
            if self.main.rt_col:
                self.main.rt_col.setStyleSheet(s)
            self.main.main.setStyleSheet(s)
        #
        # update config
        #
        if (
            self.main.config
            and self.main.config.config_panel
            and self.main.config.config_panel.forms
        ):
            for form in self.main.config.config_panel.forms:
                form.update_dark()

        #
        # update the AI tab
        #
        self.main.ai_query_tab.update_style()

        #
        # schedule an update for the splitters
        #
        if self.main.rt_col_helpers:
            self.main.rt_col_helpers.update()
        if self.main.rt_col:
            self.main.rt_col.update()
        self.main.main.update()
        self.main.centralWidget().update()
        #
        # handle the file trees specially. there is probably a better way.
        #
        if self.main.sidebar_rt_top:
            self.main.sidebar_rt_top.update_style()
        if self.main.sidebar_rt_mid:
            self.main.sidebar_rt_mid.update_style()
        if self.main.sidebar_rt_bottom:
            self.main.sidebar_rt_bottom.update_style()
        #
        # walk through the open files
        #
        if self.main.content and self.main.content.tab_widget:
            for t in taut.tabs(self.main.content.tab_widget):
                stut.set_editable_background(t)

    def do_connects(self) -> None:
        #
        # TODO / CAUTION!
        # be aware that this setup method is called at every project change
        # that means we are accumulating connects. atm, not a big problem.
        #
        self.main.rt_tab_widget.currentChanged.connect(self.on_rt_tab_changed)
        self.main.main_layout.currentChanged.connect(self.on_stack_change)
        self.main.content.tab_widget.currentChanged.connect(self.on_content_tab_changed)
        self.main.welcome.clicked.connect(self.main.welcome.on_click)
        self.main.sidebar.file_navigator.clicked.connect(self.on_tree_click)
        self.main.config.toolbar.button_close.clicked.connect(self.on_close_config)
        self.main.config.toolbar.button_cancel_changes.clicked.connect(
            self.on_cancel_config_changes
        )
        self.main.config.toolbar._button_save.clicked.connect(
            self.on_save_config_changes
        )
        self.main.sidebar.file_navigator.empty_area_click.connect(
            self.on_click_project_top
        )
        self.main.sidebar.icon_label.clicked.connect(self.on_show_welcome_screen)

    def on_click_project_top(self) -> None:
        self.main.sidebar.file_navigator.selectionModel().clear()

    def on_data_toolbar_show(self) -> None:
        self.main.show_now_or_later(self.main.content.toolbar)

    def on_data_toolbar_hide(self) -> None:
        self.main.content.toolbar.hide()

    def on_content_tab_changed(self) -> None:
        self.on_rt_tab_changed()

    def on_show_welcome_screen(self) -> None:
        self.main.show_welcome_screen()

    def on_cancel_config_changes(self) -> None:
        self.main.cancel_config_changes()

    def on_save_config_changes(self) -> None:
        self.main.save_config_changes()

    def on_close_config(self) -> None:
        self.main.close_config()

    def on_ai_gen_csvpath(self) -> None:
        self.on_ai_gen("validation")

    def on_ai_gen_data(self) -> None:
        self.on_ai_gen("testdata")

    def on_ai_ask_question(self) -> None:
        self.on_ai_gen("question")

    def on_ai_explain(self) -> None:
        self.on_ai_gen("explain")

    def on_ai_gen(self, activity="validation") -> None:
        self.main.rt_tab_widget.setCurrentIndex(1)
        self.main.rt_tab_widget.widget(1).form.activity_selector.set_activity(activity)

    # ==========================

    def on_rt_tab_changed(self) -> None:
        #
        # find if we're looking at the AI tab. if we are, find the currently visible doc's path.
        # if the doc is .csv/data set the buttons accordingly. if csvpath, likewise. if neither,
        # disable the buttons
        #
        i = self.main.rt_tab_widget.currentIndex()
        w = self.main.rt_tab_widget.widget(i)
        if isinstance(w, QueryTabWidget):
            query_tab = w
            doc = self.main.current_doc_tab
            if doc is not None:
                e = Path(doc.objectName()).suffix
                e = e.lstrip(".")
                query_tab.enable_for_extension(e)
            query_tab.form.assure_state()
            #
            # only alert on missing config if AI tab selected. we
            # don't check api_base because LiteLLM doesn't always
            # require base.
            #
            m = self.main.csvpath_config.get(section="llm", name="model")
            # k = self.main.csvpath_config.get(section="llm", name="api_key")
            if str(m).strip() in ["None", ""]:
                meut.yesNo2(
                    parent=self.main,
                    title="Incomplete AI Config",
                    msg="AI config requires at least a model name. Open AI configuration?",
                    callback=self._open_ai_config,
                )

    @Slot(int)
    def _open_ai_config(self, doit: int) -> None:
        if doit == QMessageBox.Yes:
            self.main.open_ai_config()

    # ==========================

    def on_stack_change(self) -> None:
        i = self.main.main_layout.currentIndex()
        if i == 2:
            #
            # if config and config hasn't been setup yet we need get on that.
            #
            if self.main.main_layout.widget(2).ready is False:
                self.main.main_layout.widget(2).config_panel.setup_forms()
            #
            # make sure we show the right info from the new csvpath_config. sidebar
            # will have made/triggered the update to csvpath_config of the current proj
            #
            self.main.config.config_panel.ready = False
            self.main.config.config_panel.populate_all_forms()
        #
        # if i == 2 (Config) we have to check if the config has changed. if it has
        # and we switch away work could be lost. we need to confirm w/user that is
        # ok.
        #
        if i != 2:
            self.main.question_save_config_if()
        if i in [0, 2]:
            self.main.rt_tabs_hide()
        else:
            #
            # we're switching to data or a csvpath file. that means we show the helper tab
            # and make both visible in the tabbar. if we haven't shown the tabbar before we
            # don't have a populated helper tree, so we need to get on that.
            #
            if self.main.launch_shows is not None:
                self.main.launch_shows.append(self.main.rt_tabs_show)
            else:
                self.main.rt_tabs_show()
            if self.main.rt_col_helpers.count() == 0:
                #
                # functs is the tree of functions and other help text
                #
                self.main.sidebar_functs = SidebarFunctions(main=self.main)
                self.main.rt_col_helpers.addWidget(self.main.sidebar_functs)
                #
                # add docs below functions. this panel displays content selected in the tree above it
                #
                self.main.sidebar_docs = SidebarDocs(
                    main=self.main, functions=self.main.sidebar_functs.functions
                )
                self.main.rt_col_helpers.addWidget(self.main.sidebar_docs)

    # ==========================

    def on_selected_number_of_lines_changed(self) -> None:
        """
        #
        # this is the obvious place for enabling/disabling the sample
        # method based on the number of rows; however, both
        # on_data_rows_changed and datatoolbar.enable() and disable()
        # are/may be called after this fires. rather than recall this
        # from those, we know the toolbar fires last (partly because
        # file is loaded at the end of on_data_rows_changed) so do this
        # there.
        #
        t = self.main.content.toolbar.rows.currentText()
        e = t == self.main.content.toolbar.ALL_LINES
        if e:
            self.main.content.toolbar.sampling.setEnabled(False)
        else:
            self.main.content.toolbar.sampling.setEnabled(True)
        """

    def on_data_rows_changed(self) -> None:
        t = self.main.content.toolbar.rows.currentText()
        if t == "All lines":
            #
            # set the sampling options to first-n and remove or disable others
            #
            self.main.content.toolbar.sampling.setCurrentIndex(0)
            self.main.content.toolbar.sampling.model().item(0).setEnabled(False)
            self.main.content.toolbar.sampling.model().item(1).setEnabled(False)
            self.main.content.toolbar.sampling.model().item(2).setEnabled(False)
            #
            # select first-n
            #
        else:
            self.main.content.toolbar.sampling.model().item(0).setEnabled(True)
            self.main.content.toolbar.sampling.model().item(1).setEnabled(True)
            self.main.content.toolbar.sampling.model().item(2).setEnabled(True)
            #
            # add/enable all sampling options
            #
        #
        # tell data to reload. the worker will known what to do about
        # sampling and number of lines
        #
        self.main.read_validate_and_display_file()

    # ==========================

    @Slot(QModelIndex)
    def on_tree_click(self, index):
        if not index.isValid():
            return
        source_index = self.main.sidebar.proxy_model.mapToSource(index)
        if not source_index.isValid():
            return
        file_info = self.main.sidebar.file_model.fileInfo(source_index)
        #
        # file_info.filePath sometimes allows a // to prefix the path on Mac. not
        # sure why that should be, keeping in mind we don't populate the paths in the
        # file view by hand. regardless for now, just switching to canonical and
        # moving on.
        #
        self.main.selected_file_path = file_info.canonicalFilePath()
        nos = Nos(self.main.selected_file_path)
        if not nos.isfile():
            return
        info = QFileInfo(self.main.selected_file_path)
        editable = info.suffix() in self.main.csvpath_config.get(
            section="extensions", name="csvpath_files"
        )
        editable = editable or info.suffix() in self.main.csvpath_config.get(
            section="extensions", name="csv_files"
        )
        editable = editable or info.suffix() in ["json", "md", "txt", "log"]
        if editable is True:
            editable = EditStates.EDITABLE
        else:
            editable = EditStates.UNEDITABLE
        #
        # if we are swapping one open view for another based on a tree click (e.g.
        # jsonl open as json with a click on the same file to open in grid) do we
        # need to check here and close the original first, before continuing? if
        # we don't, it would seem that we have a problem where there could be multiple
        # tabs for the same path.
        #
        # are we checking for an open tab, or just reloading?
        #
        t = taut.find_tab(self.main.content.tab_widget, nos.path)
        if t is not None:
            #
            #
            #
            if isinstance(t[1], JsonViewer2):
                #
                # close so we can reopen
                #
                self.main.content.tab_widget.close_tab(nos.path)
            else:
                taut.select_tab(self.main.content.tab_widget, t[0])
                self.main.main_layout.setCurrentIndex(1)
                return
        #
        #
        #
        self.main.read_validate_and_display_file(editable=editable)
        self.main.statusBar().showMessage(f"  {self.main.selected_file_path}")
        #
        # store the index for use in the case the user clicks off the current file
        # but then responds no to a confirm box.
        #
        self.main.sidebar.last_file_index = index

    # ==========================

    def on_help_click(self) -> None:
        ss = self.main.main.sizes()
        if ss[1] > 0:
            self.main.main.setSizes([1, 0])
        else:
            self.main.main.setSizes([4, 1])

    # ==========================

    def on_set_cwd_click(self):
        caption = "FlightPath requires a project directory. Please pick one."
        home = str(Path.home())
        path = QFileDialog.getExistingDirectory(
            self, caption, options=QFileDialog.Option.ShowDirsOnly, dir=home
        )
        if path:
            if self.main.is_writable(path):
                self.main.state.cwd = path
            else:
                meut.warning2(
                    parent=self.main,
                    title="Not writable",
                    msg=f"{path} is not a writable location. Please pick another.",
                    callback=self.main.on_set_cwd_click,
                )

    def on_reload_data(self) -> None:
        self.main.read_validate_and_display_file()

    def on_set_delimiter(self) -> None:
        self.main.read_validate_and_display_file()

    def on_set_quotechar(self) -> None:
        self.main.read_validate_and_display_file()

    def on_raw_source(self) -> None:
        index = self.main.content.tab_widget.currentIndex()
        t = self.main.content.tab_widget.widget(index)
        path = t.objectName()
        filepath = Path(path)
        ext = filepath.suffix
        if ext in [".jsonl", ".jsonlines", ".ndjson"]:
            self.main.sidebar._do_edit_as_json(path)
        else:
            t.toggle_grid_raw()

    def on_file_info(self) -> None:
        index = self.main.content.tab_widget.currentIndex()
        t = self.main.content.tab_widget.widget(index)
        path = t.objectName()

        inspector = Inspector(main=self.main, filepath=path)
        inspector.sample_size = 50
        inspector.from_line = 1

        t = fiut.make_app_path(
            f"assets{os.sep}help{os.sep}templates{os.sep}file_details.html"
        )
        html = HtmlGenerator.load_and_transform(t, inspector.info)

        info = taut.find_tab(self.main.helper.help_and_feedback, "File Info")
        if info is None:
            info = QWidget()
            info.setObjectName("FileInfo")
            self.main.helper.help_and_feedback.addTab(info, "File Info")
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        info.setLayout(layout)
        te = QTextEdit()
        layout.addWidget(te)
        te.setText(html)
        taut.select_tab_widget(self.main.helper.help_and_feedback, info)
        self.main.config.show_help()

    def on_save_sample(self) -> None:
        index = self.main.content.tab_widget.currentIndex()
        t = self.main.content.tab_widget.widget(index)
        path = t.objectName()
        source = path
        name = None
        nos = Nos(path)
        if path.endswith("xlsx") or path.endswith("xls"):
            path = path[0 : path.rfind(".")]
            path = f"{path}.csv"
        if nos.isfile():
            name = os.path.basename(path)
            path = os.path.dirname(path)
        else:
            name = "sample.csv"
        #
        # get current tab data
        #
        layout = t.layout()
        w = layout.itemAt(0).widget()
        m = w.model()
        data = m.get_data()
        #
        #
        #
        path = self.main.save_sample(path=path, name=name, data=data)
        #
        # reload views with new file
        # set the file tree to highlight the new file
        #
        if path is not None:
            self.main.read_validate_and_display_file_for_path(path=path)
            #
            # i have a path str
            # i need the proxy model index at that path
            #   1. get file_model index at path
            #   2. get proxy model index mapped to source model index
            # give proxy model index to tree_view to select
            #
            index = self.main.sidebar.file_model.index(path)
            pindex = self.main.sidebar.proxy_model.mapFromSource(index)
            if index.isValid():
                self.main.sidebar.file_navigator.setCurrentIndex(pindex)

        self.main.content.tab_widget.close_tab(source)

    # ==========================

    def on_config_changed(self):
        if hasattr(self.main, "config") and self.main.config:
            self.main.config.toolbar.button_close.setEnabled(False)
            self.main.config.toolbar.button_cancel_changes.setEnabled(True)
            self.main.config.toolbar.enable_save()
