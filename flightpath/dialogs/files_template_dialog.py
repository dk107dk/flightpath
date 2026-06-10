from .template_dialog import TemplateDialog


class FilesTemplateDialog(TemplateDialog):
    def __init__(self, *, main, name, parent, ttype="paths"):
        super().__init__(parent=parent, main=main, name=name)
        self.setWindowTitle(f"Add a File Staging Template To {name}")

        mgr = self.csvpaths.file_manager
        t = mgr.describer.get_template(self.name)
        if t is not None and str(t).strip() != "":
            self.template_ctl.setText(t)

    def do_set(self) -> None:
        self._do_set(end=":filename", mgr=self.csvpaths.file_manager)
