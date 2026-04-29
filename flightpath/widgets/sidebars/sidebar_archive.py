import os
import json
import re

from PySide6.QtWidgets import QMenu, QVBoxLayout, QTabWidget
from PySide6.QtGui import QAction, QColor
from PySide6.QtCore import Qt, Slot
from PySide6.QtWidgets import QAbstractItemView, QHeaderView

from csvpath.util.nos import Nos
from csvpath.util.path_util import PathUtility as pathu
from csvpath.util.config import Config
from csvpath.util.file_readers import DataFileReader

from flightpath.widgets.accordion.query_accordion import QueryAccordionWidget
from flightpath.widgets.sidebars.sidebar_archive_listener import SidebarArchiveListener
from flightpath.widgets.file_tree_model.treemodel import TreeModel
from flightpath.widgets.help.plus_help import HelpHeaderView
from .sidebar_archive_ref_maker import SidebarArchiveRefMaker
from flightpath.util.message_utility import MessageUtility as meut
from flightpath.util.tabs_utility import TabsUtility as taut

from flightpath.dialogs.reference_files.reference_file_handler import (
    ReferenceFileHandler,
)
from flightpath.dialogs.run_info_dialog import RunInfoDialog
from flightpath.dialogs.run_failed_dialog import RunFailedDialog

from .sidebar_right_base import SidebarRightBase
from flightpath.widgets.file_tree_model.lazy_treeview import LazyTreeView


class SidebarArchive(SidebarRightBase):
    def __init__(self, *, role=1, main, config: Config, tabs=None):
        super().__init__(parent=main)
        self.role = role
        self.main = main
        self.config = main.config if config is None else config
        self.archive_path = None
        self.setMinimumWidth(300)
        self.context_menu = None
        self.view = None
        self.model = None
        self.runs = None
        if tabs is None:
            self.tabs = QTabWidget(parent=self)
            self.runs = QueryAccordionWidget(self)
            self.runs.itemClicked.connect(self.on_item_clicked)
            self.runs.itemCloseRequested.connect(self.on_item_close_requested)
            self.runs.itemInfoRequested.connect(self.on_item_info_requested)
            self.runs.setObjectName("runs")
            #
            # show tabs method(s) will setup for viewing. here we're just creating
            # it offstage.
            #
            self.tabs.addTab(self.runs, "Runs")
            self.tabs.hide()
        else:
            self.tabs = tabs
            t = taut.find_tab(self.tabs, "runs")
            self.runs = t[1]
            self.runs.itemClicked.connect(self.on_item_clicked)
            self.runs.itemCloseRequested.connect(self.on_item_close_requested)
            self.runs.itemInfoRequested.connect(self.on_item_info_requested)
        self.setup()
        #
        # this sets up the run tabs, but we don't show them immediately
        #
        self.show_tabs()
        #
        # sftp is easy to screw up because it requires a server path + the integration fields.
        # it is also easy to check, so we do if we're looking at sftp. True means Ok or N/A.
        #
        if self.check_sftp(self.config.get(section="results", name="archive")) is False:
            meut.warning2(
                parent=self,
                title="Check SFTP",
                msg="SFTP is used for archive but not configured",
            )

    def run_ended(self, cid: str, error: bool) -> None:
        for _ in self.runs.items:
            _cid = _.metadata.get("cid")
            if _cid == cid:
                if error:
                    _.status_dot.setColor(QColor("#fa5252"))  # red
                else:
                    _.status_dot.setColor(QColor("#40c057"))  # green
                _.status = "done"
                break
        self.runs.beep()

    def on_query_submitted(self, params):
        #
        # get the id(csvpaths) in order to wire together items and run workers
        #
        cid = params.get("cid")
        csvpaths = params.get("csvpaths")
        if csvpaths is None:
            raise ValueError("CsvPaths instance cannot be None")
        metadata = {
            "id": params["worker"],
            "params": params,
            "activity": "",
            "results": None,
            "cid": cid,
            "csvpaths": csvpaths,
        }
        if "named_paths_name" in params:
            named_paths_name = params["named_paths_name"]
        named_file_name = ""
        if "named_file_name" in params:
            named_file_name = params["named_file_name"]
        title = f"{named_paths_name} results for {named_file_name}"
        #
        # add item representing the run
        #
        item = self.runs.add_item(
            title=title,
            activity="",
            status_color=QColor("#ffd43b"),
            status="pending",
            metadata=metadata,
        )
        params["item"] = item
        #
        # the item will listen for results events. we replace the items metadata_update
        # method with a simple one that handles just this specific case.
        #
        # this is no good. if another run is triggered self.main.csvpaths would (presumably) be different
        # we're going to create the csvpaths outside the run worker, pass it in, and pass it back to the
        # list directly. avoiding this, and also the csvpath coming from the worker itself, which can
        # be destroyed before the csvpaths is used
        #
        # sadly error_manager isn't working. since we have a good alternative for errors
        # i'm not digging into it.
        #
        # csvpaths.error_manager.add_internal_listener(item)
        #
        csvpaths.results_manager.dynamic_results_listeners.append(item)
        lst = SidebarArchiveListener(item=item)
        item.add_listener(lst)
        #
        # flip to the runs
        #
        self.tabs.setCurrentIndex(1)
        self.show_tabs()
        return item

    def on_run_started(self, metadata: dict):
        #
        # the accordion item is a csvpath listener. but that doesn't provide
        # a reference to the csvpath instance. and we don't get that w/
        # on_query_submitted() either. we need the instance so that we can let
        # the item open info about the running csvpaths and the csvpath objects
        # it holds.
        #
        cid = metadata.get("cid")
        if cid is None:
            raise ValueError("CsvPaths ID cannot be None")
        for _ in self.runs.items:
            acid = _.metadata.get("cid")
            if acid == cid:
                #
                # csvpaths should already be in metadata. this changed so that we aren't
                # passing state through the worker. the worker's lifecycle is unpredictable
                # relative to the sidebar and the object-delete race can result in the app
                # crashing. we'll put a check here to make sure we make noise if i missed
                # something.
                #
                # paths = metadata.get("csvpaths")
                # if paths is None:
                #    raise ValueError("CsvPaths cannot be None")
                # _.metadata["csvpaths"] = paths
                #
                if "csvpaths" not in _.metadata:
                    raise ValueError("CsvPaths instance must be available in metadata")
                _.status = "running"

    def on_item_clicked(self, metadata: dict):
        run_dir = metadata.get("run_dir")
        status = metadata.get("status")
        #
        # nothing if an error
        #
        if status == "error" and run_dir is None:
            #
            # show error?
            #
            self.on_item_info_requested(metadata)
            return
        #
        # if we don't have a run_dir nothing happened. same behavior regardless if known
        # to be an error. we shouldn't get here.
        #
        if run_dir is None:
            return
        #
        # flip to results
        #
        self.tabs.setCurrentIndex(0)
        #
        # get the status
        #
        rfh = ReferenceFileHandler(main=self.main, parent=self)
        rfh._show_run_dir_for_path(self, run_dir)

    def on_item_close_requested(self, metadata: dict):
        self.runs.remove_item(metadata)

    @Slot(dict)
    def on_item_info_requested(self, metadata: dict):
        cid = metadata.get("cid")
        for _ in self.runs.items:
            mycid = _.metadata.get("cid")
            if mycid == cid:
                if _.metadata.get("run_dir") is None:
                    d = RunFailedDialog(main=self.main, parent=self, item=_, cid=cid)
                else:
                    d = RunInfoDialog(main=self.main, parent=self, item=_)
                d.show_dialog()
                break

    def show_tabs(self) -> None:
        if self.runs.count == 0:
            return
        #
        # make sure we're looking at tabs, they start hidden
        #
        self.tabs.show()
        #
        # clear the layout and (re)add tabs
        #
        layout = self.layout()
        if layout.indexOf(self.view) > -1:
            layout.removeWidget(self.view)
        if layout.indexOf(self.tabs) > -1:
            layout.removeWidget(self.tabs)
        layout.addWidget(self.tabs)
        #
        # results is the regular tree. we have a tree already because we were passed
        # in from a past archive sidebar, but we need to replace it with our latest
        #
        for i in range(0, self.tabs.count()):
            self.tabs.removeTab(0)
        self.view.setObjectName("results")
        self.tabs.addTab(self.view, "Results")
        self.tabs.addTab(self.runs, "Runs")
        self.tabs.setCurrentIndex(1)

    def my_root(self) -> str:
        return self.main.csvpath_config.get(section="results", name="archive")

    def setup(self, do_layout=True) -> None:
        try:
            self.archive_path = self.my_root()

            nos = Nos(self.archive_path)
            if not nos.dir_exists():
                nos.makedir()

            self.view = LazyTreeView(self, main=self.main)
            #
            #
            #
            self.view.setSelectionBehavior(
                QAbstractItemView.SelectionBehavior.SelectItems
            )
            self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
            self.view.setHorizontalScrollMode(
                QAbstractItemView.ScrollMode.ScrollPerPixel
            )
            self.view.setWordWrap(False)
            self.view.setAnimated(False)
            self.view.setAllColumnsShowFocus(True)
            self.view.setAutoScroll(True)
            self.view.setIndentation(20)
            self.view.setColumnWidth(0, 250)
            header = self.view.header()
            header.setStretchLastSection(True)
            header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)

            title = "Local results archive"
            if nos.is_sftp:
                title = "SFTP results archive"
            elif nos.is_s3:
                title = "S3 results archive"
            elif nos.is_azure:
                title = "Azure results archive"
            elif nos.is_gcs:
                title = "GCS results archive"

            self.model = TreeModel(
                headers=["Archive"],
                data=nos,
                parent=self,
                title=title,
                sidebar=self,
            )
            self.model.set_style(self.view.style())
            self.view.setModel(self.model)
            self.view.updateGeometries()

            #
            #
            #
            self.view.setHeader(
                HelpHeaderView(
                    self.view, on_help=self.main.helper.on_click_archive_help
                )
            )
            self.view.header().setSectionResizeMode(0, QHeaderView.Stretch)
            self.view.header().setFixedHeight(24)
            self.view.header().setStyleSheet("QHeaderView {font-size:13px}")
            #
            #
            #
            #
            # set up context menu
            #
            self.view.setContextMenuPolicy(Qt.CustomContextMenu)
            self.view.customContextMenuRequested.connect(self._show_context_menu)
            self._setup_view_context_menu()
            #
            # moved from main
            #
            self.view.clicked.connect(self.main.reactor.on_archive_tree_click)
            if do_layout is True:
                layout = self.layout()
                if layout is None:
                    layout = QVBoxLayout()
                layout.setSpacing(0)
                layout.setContentsMargins(1, 1, 1, 1)
                layout.addWidget(self.view)
                self.setLayout(layout)
        except Exception as e:
            meut.warning2(
                parent=self,
                title=f"{type(e)} error loading named-paths",
                msg=f"Archive error: {e}",
            )

    def refresh(self) -> None:
        v = None
        if self.tabs is None:
            if self.view:
                layout = self.layout()  # Get the existing layout
                if layout:
                    layout.removeWidget(self.view)
            v = self.view
            self.view = None
            self.setup()
        else:
            self.tabs.removeTab(0)
            v = self.view
            self.view = None
            self.setup(do_layout=False)
            self.tabs.insertTab(0, self.view, "Results")
        v.deleteLater()  # Delete the old widget

    def _setup_view_context_menu(self):
        self.context_menu = QMenu(self)

        self.new_run_action = QAction()
        self.new_run_action.setText(self.tr("New run"))
        self.new_run_action.triggered.connect(self._new_run)

        self.repeat_run_action = QAction()
        self.repeat_run_action.setText("Repeat run")
        self.repeat_run_action.triggered.connect(self._repeat_run)

        self.find_data_action = QAction()
        self.find_data_action.setText("Find data")
        self.find_data_action.triggered.connect(self._find_data)

        self.copy_path_action = QAction()
        self.copy_path_action.setText("Copy path")
        self.copy_path_action.triggered.connect(self._copy_path)

        self.copy_action = QAction()
        self.copy_action.setText("Copy to working dir")
        self.copy_action.triggered.connect(self._copy_back_to_cwd)

        self.delete_action = QAction()
        self.delete_action.setText("Permanent delete")
        self.delete_action.triggered.connect(self._delete_archive_view_item)

        self.context_menu.addAction(self.repeat_run_action)
        self.context_menu.addAction(self.new_run_action)
        self.context_menu.addAction(self.find_data_action)
        self.context_menu.addAction(self.copy_path_action)
        self.context_menu.addAction(self.copy_action)
        self.context_menu.addSeparator()
        self.context_menu.addAction(self.delete_action)

    def _results_mani_path_for_path(self, path: str) -> str:
        if path is None:
            raise ValueError("Path cannot be None")
        #
        # we need the archive path as one thing; otherwise, we're likely to have trouble with the protocol.
        #
        apath = path[len(self.archive_path) + 1 :]
        parts = pathu.parts(apath)
        parts = [self.archive_path] + parts
        sep = pathu.sep(path)
        maniparts = []
        found = False
        for part in parts:
            m = re.search(r"^.*\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}(?:_\d)?", part)
            maniparts.append(part)
            if m is not None:
                found = True
                break
        if found is False:
            self._find_manifest_below(maniparts, path)
        else:
            maniparts.append("manifest.json")
        ret = sep[0].join(maniparts)
        return ret

    def _find_manifest_below(self, maniparts: list[str], path: str) -> None:
        nos = Nos(path)
        lst = nos.listdir(recurse=True, files_only=True)
        mani = None
        for _ in lst:
            if _.endswith("manifest.json"):
                if mani is None or len(_) < len(mani):
                    mani = _
        if mani is not None:
            maniparts.clear()
            maniparts.append(mani)
        else:
            raise ValueError(f"Cannot find manifest below {path}")

    def _is_archive_manifest(self, path: str) -> bool:
        config = self.main.csvpath_config
        archive = config.get(section="results", name="archive")
        arcmani = f"{archive}{os.sep}manifest.json"
        if path and path.strip() == arcmani:
            return True
        return False

    def _has_reference(self, path) -> bool:
        if path is None:
            raise ValueError("Path cannot be None")
        try:
            #
            # need to check if this is the archive/manifest.json. if it is return False
            #
            if self._is_archive_manifest(path):
                return False
            #
            #
            #
            manipath = self._results_mani_path_for_path(path)
            mani = None
            with DataFileReader(manipath) as file:
                mani = json.load(file.source)
            if "$" in mani["named_file_name"] or "$" in mani["named_paths_name"]:
                return True
            return False
        except Exception as e:
            #
            # if we're in the middle of a template, not on a specific result, we don't want a repeat run.
            # however, we can't say if there is a refrence or not because we're not on a run we can check.
            # in that case we throw an exception rather than being more perceptive about it. which is
            # fineish. therefore this isn't a binary, it's a ternary, which kind of sucks, but we get the
            # 3rd state by returning None.
            #
            print(f"No reference found because {type(e)}: {e}. This is probably fine.")
            return None

    def _show_context_menu(self, position):
        index = self.view.indexAt(position)
        path = None
        if index.isValid():
            global_pos = self.view.viewport().mapToGlobal(position)
            path = self.model.filePath(index)
            self._last_path = path
            nos = Nos(path)
            #
            # individual files may not be deleted, but we can allow dir deletes for cleanup
            #
            if nos.isfile():
                self.delete_action.setVisible(False)
                self.new_run_action.setVisible(True)
                if self._has_reference(path) is False:
                    self.repeat_run_action.setVisible(True)
                else:
                    self.repeat_run_action.setVisible(False)
                self.find_data_action.setVisible(True)
                self.copy_path_action.setVisible(True)
                self.copy_action.setVisible(True)
            else:
                self.delete_action.setVisible(True)
                self.new_run_action.setVisible(True)
                if self._has_reference(path) is False:
                    self.repeat_run_action.setVisible(True)
                else:
                    self.repeat_run_action.setVisible(False)
                self.find_data_action.setVisible(True)
                self.copy_path_action.setVisible(True)
                self.copy_action.setVisible(False)
            if path and (path.endswith("manifest.json") or path.endswith(".db")):
                self.delete_action.setVisible(False)
                self.new_run_action.setVisible(False)
                self.repeat_run_action.setVisible(False)
                self.find_data_action.setVisible(False)
                self.copy_path_action.setVisible(False)
                self.copy_action.setVisible(True)
            if global_pos:
                self.context_menu.exec(global_pos)

    def _new_run(self) -> None:
        maker = SidebarArchiveRefMaker(main=self.main, parent=self)
        maker._new_run()

    def _repeat_run(self) -> None:
        maker = SidebarArchiveRefMaker(main=self.main, parent=self)
        maker._repeat_run()
