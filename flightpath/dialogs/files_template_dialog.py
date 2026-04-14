"""
from PySide6.QtWidgets import ( # pylint: disable=E0611
        QVBoxLayout,
        QHBoxLayout,
        QPushButton,
        QDialog,
        QLineEdit,
        QFormLayout,
        QSizePolicy,
        QWidget
)
from PySide6.QtCore import Qt # pylint: disable=E0611
"""

from .template_dialog import TemplateDialog


class FilesTemplateDialog(TemplateDialog):
    def __init__(self, *, main, name, parent, ttype="paths"):
        super().__init__(parent=parent, main=main, name=name)
        self.setWindowTitle(f"Add a file staging template to {name}")

        mgr = self.csvpaths.file_manager
        t = mgr.describer.get_template(self.name)
        if t is not None and str(t).strip() != "":
            self.template_ctl.setText(t)

    def do_set(self) -> None:
        t = self.template_ctl.text()
        mgr = self.csvpaths.file_manager
        mgr.describer.store_template(self.name, t)

        #
        # if we updated the file we need to make sure it's closed before we click on it
        # otherwise segfault.
        #
        if self.tab is not None:
            self.main.content.tab_widget.close_tab(self.tab.objectName())
            self.tab = None
        #
        #
        #
        self.close()
