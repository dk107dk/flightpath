from PySide6.QtWidgets import QMenu, QVBoxLayout

from PySide6.QtGui import QAction
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QAbstractItemView, QHeaderView

from csvpath import CsvPaths
from csvpath.util.nos import Nos
from csvpath.util.config import Config
from csvpath.util.path_util import PathUtility as pathu


from flightpath.widgets.file_tree_model.treemodel import TreeModel
from flightpath.widgets.file_tree_model.lazy_treeview import LazyTreeView

from flightpath.dialogs.new_run_dialog import NewRunDialog
from flightpath.dialogs.paths_template_dialog import PathsTemplateDialog
from flightpath.dialogs.find_file_by_reference_dialog import FindFileByReferenceDialog
from flightpath.dialogs.webhooks_dialog import WebhooksDialog

from flightpath.widgets.help.plus_help import HelpHeaderView
from flightpath.util.message_utility import MessageUtility as meut
from flightpath.editable import EditStates
from .sidebar_right_base import SidebarRightBase


class SidebarNamedPaths(SidebarRightBase):
    def __init__(self, *, main, role=1, config: Config):
        super().__init__(parent=main)
        self.main = main
        self.config = main.config if config is None else config
        self.setMinimumWidth(300)
        self.new_run_action = None
        self.copy_action = None
        self.delete_action = None
        self.find_data_action = None
        self.view = None
        self.model = None
        #
        # sftp is easy to screw up because it requires a server path + the integration fields.
        # it is also easy to check, so we do if we're looking at sftp. True means Ok or N/A.
        #
        if self.check_sftp(self.config.get(section="inputs", name="csvpaths")) is True:
            self.setup()
        else:
            meut.warning(
                parent=self, title="Check SFTP", msg="SFTP is used but not configured"
            )

    def my_root(self) -> str:
        return self.main.csvpath_config.get(section="inputs", name="csvpaths")

    def setup(self) -> None:
        try:
            named_paths_path = self.my_root()

            nos = Nos(named_paths_path)
            layout = self.layout()
            if layout is None:
                layout = QVBoxLayout()
            layout.setSpacing(0)
            layout.setContentsMargins(1, 1, 1, 1)
            #
            # do we really need to do this dir create here?
            #
            if not nos.dir_exists():
                nos.makedir()
            self.view = LazyTreeView(self, main=self.main)

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

            title = "Csvpaths loaded locally"
            nos = Nos(named_paths_path)
            if nos.is_sftp:
                title = "Csvpaths loaded in SFTP"
            elif nos.is_s3:
                title = "Csvpaths loaded in S3"
            elif nos.is_azure:
                title = "Csvpaths loaded in Azure"
            elif nos.is_gcs:
                title = "Csvpaths loaded in GCS"

            self.model = TreeModel(
                headers=["Csvpath groups"],
                data=nos,
                parent=self,
                title=title,
                sidebar=self,
            )
            self.model.set_style(self.view.style())
            self.view.setModel(self.model)
            self.view.updateGeometries()
            layout.addWidget(self.view)
            #
            #
            #
            self.view.setHeader(
                HelpHeaderView(
                    self.view, on_help=self.main.helper.on_click_named_paths_help
                )
            )
            self.view.header().setSectionResizeMode(0, QHeaderView.Stretch)
            self.view.header().setFixedHeight(24)
            self.view.header().setStyleSheet("QHeaderView {font-size:13px}")
            #
            #
            #
            self.view.setContextMenuPolicy(Qt.CustomContextMenu)
            self.view.customContextMenuRequested.connect(self._show_context_menu)
            self._setup_view_context_menu()
            #
            # moved from main
            #
            self.view.clicked.connect(self.on_named_paths_tree_click)
            self.setLayout(layout)
        except Exception as e:
            meut.warning(
                parent=self,
                title=f"{type(e)} error loading named-paths",
                msg=f"Named-paths error: {e}",
            )

    #
    # moved from main
    #
    def on_named_paths_tree_click(self, index):
        self.main.selected_file_path = self.model.filePath(index)
        nos = Nos(self.main.selected_file_path)
        if not nos.isfile():
            ...
            # self._show_welcome_but_do_not_deselect()
        else:
            ed = (
                EditStates.EDITABLE
                if self.main.selected_file_path.endswith(".md")
                else EditStates.UNEDITABLE
            )
            self.main.read_validate_and_display_file(editable=ed)
            self.main.statusBar().showMessage(f"  {self.main.selected_file_path}")

    def refresh(self) -> None:
        if self.view:
            layout = self.layout()  # Get the existing layout
            if layout:
                layout.removeWidget(self.view)
            self.view.deleteLater()  # Delete the old widget
            self.setup()

    def _setup_view_context_menu(self):
        self.context_menu = QMenu(self)

        self.new_run_action = QAction()
        self.new_run_action.setText("New run")
        self.new_run_action.triggered.connect(self._new_run)

        self.copy_action = QAction()
        self.copy_action.setText("Copy to working dir")
        self.copy_action.triggered.connect(self._copy_back_to_cwd)

        self.template_action = QAction()
        self.template_action.setText("Set template")
        self.template_action.triggered.connect(self._template)

        self.webhook_action = QAction()
        self.webhook_action.setText("Set webhooks")
        self.webhook_action.triggered.connect(self._webhooks)

        self.delete_action = QAction()
        self.delete_action.setText("Permanent delete")
        self.delete_action.triggered.connect(self._delete_file_navigator_item)

        self.find_data_action = QAction()
        self.find_data_action.setText("Find data")
        self.find_data_action.triggered.connect(self._find_data)

        self.context_menu.addAction(self.new_run_action)
        self.context_menu.addAction(self.copy_action)
        self.context_menu.addAction(self.template_action)
        self.context_menu.addAction(self.webhook_action)
        self.context_menu.addAction(self.find_data_action)
        self.context_menu.addSeparator()
        self.context_menu.addAction(self.delete_action)

    @property
    def _paths_root(self) -> str:
        return self.main.csvpath_config.get(section="inputs", name="csvpaths")

    def _new_run(self) -> None:
        index = self.view.currentIndex()
        path = self.model.filePath(index)
        named_paths = None
        if path.startswith(self._paths_root):
            named_paths = path[len(self._paths_root) + 1 :]
        else:
            # shouldn't happen but what if it did?
            ...
        self.new_run_dialog = NewRunDialog(parent=self, named_paths=named_paths)
        #
        # check if there is a description.json. if there is, check if
        # there is a template for the group. if so, add to dialog.
        #
        t = CsvPaths().paths_manager.get_template_for_paths(named_paths)
        if t:
            self.new_run_dialog.template = t
            self.new_run_dialog.template_ctl.setText(t)
        self.main.show_now_or_later(self.new_run_dialog)

    def _show_context_menu(self, position) -> None:
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
            if nos.isfile() and path.endswith("definition.json"):
                self.delete_action.setVisible(False)
                self.new_run_action.setVisible(True)
                self.webhook_action.setVisible(True)
                self.copy_action.setVisible(True)
                self.template_action.setVisible(True)
                self.find_data_action.setVisible(True)
            elif nos.isfile():
                self.delete_action.setVisible(False)
                self.new_run_action.setVisible(False)
                self.webhook_action.setVisible(False)
                self.copy_action.setVisible(True)
                self.template_action.setVisible(False)
                self.find_data_action.setVisible(True)
            else:
                self.delete_action.setVisible(True)
                self.new_run_action.setVisible(True)
                self.webhook_action.setVisible(True)
                self.copy_action.setVisible(False)
                self.template_action.setVisible(True)
                self.find_data_action.setVisible(True)
            if path and (path.endswith("manifest.json") or path.endswith(".db")):
                self.delete_action.setVisible(False)
                self.new_run_action.setVisible(False)
                self.copy_action.setVisible(True)
                self.find_data_action.setVisible(False)
                self.webhook_action.setVisible(False)
                self.template_action.setVisible(False)

            if global_pos:
                self.context_menu.exec(global_pos)

    def _webhooks(self) -> None:
        index = self.view.currentIndex()
        if index.isValid():
            path = self.model.filePath(index)
            r = self.main.csvpath_config.get(section="inputs", name="csvpaths")
            if not path.startswith(r):
                raise ValueError(f"Path to item {path} doesn't start with {r}")
            path = path[len(r) + 1 :]
            name = pathu.parts(path)[0]
            dialog = WebhooksDialog(main=self.main, name=name, parent=self)
            dialog.show_dialog()

    def _template(self) -> None:
        index = self.view.currentIndex()
        if index.isValid():
            path = self.model.filePath(index)
            r = self.main.csvpath_config.get(section="inputs", name="csvpaths")
            if not path.startswith(r):
                raise ValueError(f"Path to item {path} doesn't start with {r}")
            path = path[len(r) + 1 :]
            name = pathu.parts(path)[0]
            dialog = PathsTemplateDialog(main=self.main, name=name, parent=self)
            dialog.show_dialog()

    def _find_data(self) -> None:
        find = FindFileByReferenceDialog(main=self.main)
        self.main.show_now_or_later(find)

    def _delete_file_navigator_item(self) -> None:
        index = self.view.currentIndex()
        if index.isValid():
            path = self.model.filePath(index)
            nos = Nos(path)
            confirm = meut.yes_no(
                parent=self, title="Delete", msg=f"Permanently delete {path}?"
            )
            if confirm is True:
                try:
                    nos.remove()
                except OSError as e:
                    meut.warning(parent=self, title="Error", msg=str(e))
                else:
                    #
                    # TODO: this will have to change because we don't want to dismiss
                    # content that is being worked on from the working dir side
                    #
                    # if is_selected:
                    #    self.window().show_welcome_screen()
                    self.window().statusBar().showMessage(f"{path} deleted")
                    #
                    # TODO: we recreate all the trees. very bad idea due to slow refresh from remote.
                    # but for now it should work. refreshing named_files is probably fair, but that's
                    # also tricky because we'd want to recreate the opened/closed state of the folders
                    # and if we did that the refresh might slow down potentially a lot. so long-term,
                    # seems like we should capture what is registered and manually add it. no fun. :/
                    #
                    # self.main._setup_central_widget()
                    self.main.renew_sidebar_named_paths()
                    self.main.welcome.update_run_button()
                    self.main.welcome.update_find_data_button()
