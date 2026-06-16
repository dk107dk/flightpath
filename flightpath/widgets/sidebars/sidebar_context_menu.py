import os

from PySide6.QtWidgets import QWidget, QMenu, QMainWindow
from PySide6.QtGui import QAction
from PySide6.QtCore import QModelIndex

from csvpath.util.nos import Nos


class SidebarContextMenuMaker:
    def __init__(self, *, main: QMainWindow, parent: QWidget):
        super().__init__()
        self.main = main
        self.my_parent = parent

    # -------------------------------------------------------------------------
    # Entry point
    # -------------------------------------------------------------------------

    def show_context_menu(self, position):
        index = self.my_parent.file_navigator.indexAt(position)
        global_pos = self.my_parent.file_navigator.viewport().mapToGlobal(position)
        menu = self._build_menu_for(index)
        menu.exec(global_pos)

    # -------------------------------------------------------------------------
    # Dispatcher
    # -------------------------------------------------------------------------

    def _build_menu_for(self, index: QModelIndex) -> QMenu:
        if not index.isValid():
            return self._build_empty_space_menu()
        path = self.my_parent.proxy_model.filePath(index)
        self.my_parent._last_path = path
        if Nos(path).isfile():
            return self._build_file_menu(path)
        else:
            return self._build_directory_menu(path)

    # -------------------------------------------------------------------------
    # Per-context builders
    # -------------------------------------------------------------------------

    def _build_file_menu(self, path: str) -> QMenu:
        ext = path.rsplit(".", 1)[-1].lower() if "." in path else ""
        menu = QMenu(self.my_parent)

        self._add_jsonl_actions(menu, path)
        menu.addSeparator()
        self._add_standard_file_actions(menu, path)
        self._add_worksheet_submenu(menu, path)
        self._add_path_copy_actions(menu)
        menu.addSeparator()
        self._add_clipboard_actions(menu, path, ext, is_dir=False)
        menu.addSeparator()
        self._add_delete_action(menu)
        menu.addSeparator()
        self._add_generation_actions(menu, ext)
        self._add_stage_load_actions(menu, ext)
        self._add_explain_action(menu, ext)
        menu.addSeparator()
        self._add_csv_line_count_action(menu, path)

        return menu

    def _build_directory_menu(self, path: str) -> QMenu:
        menu = QMenu(self.my_parent)

        self._add_rename_action(menu)
        self._add_open_location_action(menu)
        self._add_path_copy_actions(menu)
        menu.addSeparator()
        self._add_clipboard_actions(menu, path, ext=None, is_dir=True)
        menu.addSeparator()
        self._add_delete_action(menu)
        menu.addSeparator()
        self._add_new_file_folder_actions(menu)
        menu.addSeparator()
        self._add_stage_load_actions(menu, ext=None, is_dir=True)

        return menu

    def _build_empty_space_menu(self) -> QMenu:
        """Right-clicked on blank space in the tree (no item selected)."""
        self.my_parent._last_path = None
        menu = QMenu(self.my_parent)

        self._add_new_file_folder_actions(menu)
        menu.addSeparator()
        self._add_open_project_dir_action(menu)
        menu.addSeparator()

        paste_action = QAction("Paste", menu)
        paste_action.setEnabled(bool(self.my_parent.cutted or self.my_parent.copied))
        paste_action.triggered.connect(self.my_parent.actions._paste)
        menu.addAction(paste_action)

        return menu

    # -------------------------------------------------------------------------
    # Action-group helpers
    # -------------------------------------------------------------------------

    def _add_jsonl_actions(self, menu: QMenu, path: str):
        if path.endswith((".jsonl", ".ndjson", ".jsonlines")):
            action = QAction("Edit as JSON", menu)
            action.triggered.connect(self.my_parent.actions._edit_as_json)
            menu.addAction(action)

    def _add_standard_file_actions(self, menu: QMenu, path: str):
        save = QAction("Save file", menu)
        save.triggered.connect(self.my_parent.actions._save_file_navigator_item)
        menu.addAction(save)

        rename = QAction("Rename", menu)
        rename.triggered.connect(self.my_parent.actions._rename_file_navigator_item)
        menu.addAction(rename)

        open_loc = QAction("Open directory", menu)
        open_loc.triggered.connect(self.my_parent.actions._open_file_navigator_location)
        menu.addAction(open_loc)

    def _add_rename_action(self, menu: QMenu):
        action = QAction("Rename", menu)
        action.triggered.connect(self.my_parent.actions._rename_file_navigator_item)
        menu.addAction(action)

    def _add_open_location_action(self, menu: QMenu):
        action = QAction("Open directory", menu)
        action.triggered.connect(self.my_parent.actions._open_file_navigator_location)
        menu.addAction(action)

    def _add_open_project_dir_action(self, menu: QMenu):
        action = QAction("Open project directory", menu)
        action.triggered.connect(self.my_parent.actions._open_project_dir)
        menu.addAction(action)

    def _add_path_copy_actions(self, menu: QMenu):
        rel = QAction("Copy relative path", menu)
        rel.triggered.connect(self.my_parent.actions._copy_path)
        menu.addAction(rel)

        full = QAction("Copy full path", menu)
        full.triggered.connect(self.my_parent.actions._copy_full_path)
        menu.addAction(full)

    def _add_clipboard_actions(
        self, menu: QMenu, path: str, ext: str | None, is_dir: bool
    ):
        cut = QAction("Cut", menu)
        copy = QAction("Copy", menu)
        paste = QAction("Paste", menu)

        if is_dir:
            cut.setEnabled(False)
            copy.setEnabled(False)
            paste.setEnabled(bool(self.my_parent.cutted or self.my_parent.copied))
        else:
            cuttable = ext in self._text_like_extensions()
            cut.setEnabled(cuttable)
            copy.setEnabled(cuttable)
            # Cannot paste onto a file
            paste.setEnabled(False)

        cut.triggered.connect(self.my_parent.actions._cut)
        copy.triggered.connect(self.my_parent.actions._copy)
        paste.triggered.connect(self.my_parent.actions._paste)

        menu.addAction(cut)
        menu.addAction(copy)
        menu.addAction(paste)

    def _add_delete_action(self, menu: QMenu):
        action = QAction("Delete", menu)
        action.triggered.connect(self.my_parent.actions._delete_file_navigator_item)
        menu.addAction(action)

    def _add_new_file_folder_actions(self, menu: QMenu):
        new_file = QAction("New file", menu)
        new_file.triggered.connect(self.my_parent.actions._new_file_navigator_item)
        menu.addAction(new_file)

        new_folder = QAction("New folder", menu)
        new_folder.triggered.connect(self.my_parent.actions._new_folder_navigator_item)
        menu.addAction(new_folder)

    def _add_generation_actions(self, menu: QMenu, ext: str):
        csvpath_exts = self._csvpath_extensions()
        csv_exts = self._csv_extensions()
        has_llm = self._has_llm()

        if ext in csvpath_exts or ext.lower() == "json":
            #
            # should we not do Generate CSV here?
            #
            pass  # no generation action for csvpath files
        elif ext in csv_exts:
            action = QAction("Generate csvpath", menu)
            action.setEnabled(has_llm)
            action.triggered.connect(self.my_parent.actions._generate_csvpath)
            menu.addAction(action)
        else:
            action = QAction("Generate CSV", menu)
            action.setEnabled(has_llm)
            action.triggered.connect(self.my_parent.actions._generate_csv)
            menu.addAction(action)

    def _add_stage_load_actions(
        self, menu: QMenu, ext: str | None, is_dir: bool = False
    ):
        csv_exts = self._csv_extensions()
        csvpath_exts = self._csvpath_extensions()

        if is_dir:
            stage = QAction("Stage data", menu)
            stage.triggered.connect(self.my_parent.actions._stage_data)
            menu.addAction(stage)

            load = QAction("Load csvpaths", menu)
            load.triggered.connect(self.my_parent.actions._load_paths)
            menu.addAction(load)
            return

        if ext in csv_exts:
            action = QAction("Stage data", menu)
            action.triggered.connect(self.my_parent.actions._stage_data)
            menu.addAction(action)
        elif ext in csvpath_exts or ext == "json":
            action = QAction("Load csvpaths", menu)
            action.triggered.connect(self.my_parent.actions._load_paths)
            menu.addAction(action)

    def _add_explain_action(self, menu: QMenu, ext: str):
        relevant_exts = self._csvpath_extensions() | {"json"}
        if ext in relevant_exts:
            action = QAction("Explain this", menu)
            action.setEnabled(self._has_llm())
            action.triggered.connect(self.my_parent.actions._on_explain)
            menu.addAction(action)

    def _add_worksheet_submenu(self, menu: QMenu, path: str):
        if not path.endswith(".xlsx"):
            return
        names = self.my_parent._worksheets_for_path(path)
        if not names:
            return
        submenu = QMenu("Worksheets", menu)
        for name in names:
            action = QAction(name, submenu)
            # Use a default-argument capture to bind the name at loop time
            action.triggered.connect(
                lambda checked=False, n=name: self.my_parent.actions._load_worksheet(n)
            )
            submenu.addAction(action)
        menu.addMenu(submenu)

    def _add_csv_line_count_action(self, menu: QMenu, path: str):
        if not path.endswith(".csv"):
            return
        csvpaths = self.main.csvpaths
        csvpaths.config.set(
            section="cache", name="path", value=f"{self.main.state.cwd}{os.sep}cache"
        )
        csvpaths.config.set(section="cache", name="use_cache", value="yes")
        count = csvpaths.file_manager.lines_and_headers_cacher.get_new_line_monitor(
            path
        ).physical_end_line_count
        action = QAction(f"{count} lines", menu)
        action.setEnabled(False)
        menu.addAction(action)

    # -------------------------------------------------------------------------
    # Extension helpers
    # -------------------------------------------------------------------------

    def _csvpath_extensions(self) -> set:
        return set(
            self.main.csvpath_config.get(section="extensions", name="csvpath_files")
        )

    def _csv_extensions(self) -> set:
        return set(self.main.csvpath_config.get(section="extensions", name="csv_files"))

    def _text_like_extensions(self) -> set:
        return (
            self._csvpath_extensions() | self._csv_extensions() | {"md", "json", "txt"}
        )

    # -------------------------------------------------------------------------
    # Capability check
    # -------------------------------------------------------------------------

    def _has_llm(self) -> bool:
        # Placeholder — replace with real check from parent/main
        return self.my_parent._has_llm()
