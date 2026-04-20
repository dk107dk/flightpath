import traceback

from PySide6.QtWidgets import QMenu, QMessageBox, QVBoxLayout, QSizePolicy, QApplication

from PySide6.QtGui import QAction
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QAbstractItemView, QHeaderView

from csvpath.util.nos import Nos
from csvpath.util.config import Config
from csvpath.util.path_util import PathUtility as pathu

from flightpath.widgets.file_tree_model.treemodel import TreeModel
from flightpath.widgets.file_tree_model.lazy_treeview import LazyTreeView

from flightpath.dialogs.new_run_dialog import NewRunDialog
from flightpath.dialogs.find_file_by_reference_dialog import FindFileByReferenceDialog
from flightpath.dialogs.activation_dialog import ActivationDialog
from flightpath.dialogs.files_template_dialog import FilesTemplateDialog


from .sidebar_file_ref_maker import SidebarFileRefMaker
from flightpath.widgets.help.plus_help import HelpHeaderView
from flightpath.util.message_utility import MessageUtility as meut
from flightpath.util.file_utility import FileUtility as fiut

from flightpath.editable import EditStates
from .sidebar_right_base import SidebarRightBase


class SidebarNamedFiles(SidebarRightBase):
    def __init__(self, *, main, role=1, config: Config):
        super().__init__()
        self.role = role
        self.setMinimumWidth(300)
        self.main = main
        self.view = None
        self.setup()
        self._template_dialog = None

    def my_root(self) -> str:
        return self.main.csvpath_config.get(section="inputs", name="files")

    def setup(self) -> None:
        try:
            layout = self.layout()
            if layout is None:
                layout = QVBoxLayout()
            layout.setSpacing(0)
            layout.setContentsMargins(1, 1, 1, 1)
            named_files_path = self.my_root()

            nos = Nos(named_files_path)
            try:
                if not nos.dir_exists():
                    nos.makedir()
            except Exception as ex:
                print(traceback.format_exc())
                msg = f"Error during named-files inputs setup: {ex}"
                meut.warning(parent=self, msg=msg, title="Error")
                return

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

            title = "Files staged locally"
            nos = Nos(named_files_path)
            if nos.is_sftp:
                title = "Files staged in SFTP"
            elif nos.is_s3:
                title = "Files staged in S3"
            elif nos.is_azure:
                title = "Files staged in Azure"
            elif nos.is_gcs:
                title = "Files staged in GCS"
            #
            # can we be more clear about where files are?
            #

            self.model = TreeModel(
                headers=["Staged files"],
                data=nos,
                parent=self,
                title=title,
                sidebar=self,
                tree=self.view,
            )
            self.model.set_style(self.view.style())
            self.view.setModel(self.model)
            #
            #
            #
            self.view.updateGeometries()

            layout.addWidget(self.view)
            self.view.setSizePolicy(
                QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
            )
            self.view.setContextMenuPolicy(Qt.CustomContextMenu)
            self.view.customContextMenuRequested.connect(self._show_context_menu)
            self._setup_view_context_menu()
            #
            #
            #
            self.view.setHeader(
                HelpHeaderView(
                    self.view, on_help=self.main.helper.on_click_named_files_help
                )
            )
            self.view.header().setSectionResizeMode(0, QHeaderView.Stretch)
            self.view.header().setFixedHeight(24)
            self.view.header().setStyleSheet("QHeaderView {font-size:13px}")
            #
            # moved from main
            #
            self.view.clicked.connect(self.on_named_file_tree_click)
            self.setLayout(layout)

        except Exception as e:
            print(traceback.format_exc())
            meut.warning(
                parent=self,
                title=f"{type(e)} error loading named-files",
                msg=f"Named-files error: {e}",
            )

    #
    # moved from main
    #
    def on_named_file_tree_click(self, index):
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
        # create actions
        self.new_run_action = QAction()
        self.new_run_action.setText("New run")
        self.new_run_action.triggered.connect(self._new_run)

        self.arrival_action = QAction()
        self.arrival_action.setText("Arrival activation")
        self.arrival_action.triggered.connect(self._set_activation)

        self.template_action = QAction()
        self.template_action.setText("Set template")
        self.template_action.triggered.connect(self._template)

        self.copy_path_action = QAction()
        self.copy_path_action.setText("Copy path")
        self.copy_path_action.triggered.connect(self._copy_path)

        self.find_data_action = QAction()
        self.find_data_action.setText("Find data")
        self.find_data_action.triggered.connect(self._find_data)

        self.delete_action = QAction()
        self.delete_action.setText("Permanent delete")
        self.delete_action.triggered.connect(self._delete_view_item)

        self.copy_action = QAction()
        self.copy_action.setText(self.tr("Copy to working dir"))
        self.copy_action.triggered.connect(self._copy_back_to_cwd)

        # add to menu
        self.context_menu.addAction(self.new_run_action)
        self.context_menu.addAction(self.arrival_action)
        self.context_menu.addAction(self.template_action)
        self.context_menu.addAction(self.find_data_action)
        self.context_menu.addAction(self.copy_path_action)
        self.context_menu.addAction(self.copy_action)
        self.context_menu.addSeparator()
        self.context_menu.addAction(self.delete_action)

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
            if (
                fiut.is_a(path, ["db", "md", "txt"])
                or path.endswith("manifest.json")
                or path.endswith("definition.json")
            ):
                self.copy_action.setVisible(True)
                self.copy_path_action.setVisible(False)
                self.arrival_action.setVisible(False)
                self.find_data_action.setVisible(False)
                self.delete_action.setVisible(False)
                self.new_run_action.setVisible(False)
            elif nos.isfile():
                self.copy_path_action.setVisible(True)
                self.copy_action.setVisible(True)
                self.new_run_action.setVisible(True)
                self.arrival_action.setVisible(False)
                self.template_action.setVisible(False)
                self.find_data_action.setVisible(True)
                self.delete_action.setVisible(False)
            else:
                self.copy_path_action.setVisible(True)
                self.template_action.setVisible(True)
                self.arrival_action.setVisible(True)
                self.find_data_action.setVisible(True)
                self.delete_action.setVisible(True)
                self.new_run_action.setVisible(True)
                self.copy_action.setVisible(False)
            if global_pos:
                self.context_menu.exec(global_pos)

    def _template(self) -> None:
        index = self.view.currentIndex()
        if index.isValid():
            path = self.model.filePath(index)
            r = self.main.csvpath_config.get(section="inputs", name="files")
            if not path.startswith(r):
                raise ValueError(f"Path to item {path} doesn't start with {r}")
            path = path[len(r) + 1 :]
            name = pathu.parts(path)[0]
            self._template_dialog = FilesTemplateDialog(
                main=self.main, name=name, parent=self
            )
            # When the dialog finishes, drop the reference
            self._template_dialog.finished.connect(
                lambda _: setattr(self, "_template_dialog", None)
            )
            self._template_dialog.show_dialog()

    def _copy_path(self) -> None:
        from_index = self.view.currentIndex()
        if from_index.isValid():
            path = self.model.filePath(from_index)
            clipboard = QApplication.instance().clipboard()
            clipboard.setText(path)

    def _new_run(self):
        maker = SidebarFileRefMaker(parent=self, main=self.main)
        ref = maker.new_run_ref()
        self.new_run_dialog = NewRunDialog(
            parent=self, named_paths=None, named_file=ref
        )
        self.main.show_now_or_later(self.new_run_dialog)

    def _set_activation(self):
        maker = SidebarFileRefMaker(parent=self, main=self.main)
        name = maker.named_file_name()
        self.activation_dialog = ActivationDialog(
            parent=self, main=self.main, named_file=name
        )
        self.main.show_now_or_later(self.activation_dialog)

    def _find_data(self):
        find = FindFileByReferenceDialog(main=self.main)
        self.main.show_now_or_later(find)

    def _delete_view_item(self):
        index = self.view.currentIndex()
        if index.isValid():
            path = self.model.filePath(index)
            nos = Nos(path)
            confirm = QMessageBox.question(
                self,
                self.tr("Delete"),
                self.tr(f"Permanently delete {path}?"),
                QMessageBox.Yes | QMessageBox.No,
            )
            if confirm == QMessageBox.Yes:
                try:
                    nos.remove()
                except OSError as e:
                    QMessageBox.warning(self, self.tr("Error"), str(e))
                else:
                    #
                    # TODO: this will have to change because we don't want to dismiss
                    # content that is being worked on from the working dir side
                    #
                    # if is_selected:
                    #    self.window().show_welcome_screen()
                    self.window().statusBar().showMessage("{path} deleted")
                    #
                    # TODO: we recreate all the trees. very bad idea due to slow refresh from remote.
                    # but for now it should work. refreshing named_files is probably fair, but that's
                    # also tricky because we'd want to recreate the opened/closed state of the folders
                    # and if we did that the refresh might slow down potentially a lot. so long-term,
                    # seems like we should capture what is registered and manually add it. no fun. :/
                    #
                    # self.main._setup_central_widget()
                    self.main.renew_sidebar_named_files()
                    self.main.welcome.update_run_button()
                    self.main.welcome.update_find_data_button()
