import os
from PySide6.QtWidgets import ( # pylint: disable=E0611
        QVBoxLayout,
        QHBoxLayout,
        QPushButton,
        QLabel,
        QDialog,
        QLineEdit,
        QFormLayout,
        QComboBox,
        QInputDialog,
        QSizePolicy,
        QScrollArea,
        QWidget,
        QPlainTextEdit,
        QMessageBox
)
from PySide6.QtCore import Qt, QSize
from csvpath.util.file_readers import DataFileReader
from csvpath.util.file_writers import DataFileWriter
from csvpath.util.class_loader import ClassLoader

from flightpath_generator.util.config import Config as GeneratorConfig
from flightpath_generator import Generator
from flightpath_generator.client.run_tool import LiteLLMRunTool
#from flightpath_generator.client.syntax_tool import LiteLLMSyntaxTool
from flightpath_generator.client.function_tool import LiteLLMFunctionTool

from flightpath.widgets.help.plus_help import HelpIconPackager
from flightpath.util.help_finder import HelpFinder
from flightpath.util.file_utility import FileUtility as fiut
from flightpath.util.syntax.csvpath_highlighter import CsvPathSyntaxHighlighter
from flightpath.editable import EditStates

class GenerateCsvpathDialog(QDialog):


    def __init__(self, *, parent, main, path):
        super().__init__(main)
        if path is None:
            raise ValueError("Path cannot be None")
        if main is None:
            raise ValueError("Main cannot be None")

        self.main = main
        self.path = path
        self.parent = parent

        self.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint)
        self.setWindowModality(Qt.NonModal)

        self.setWindowTitle("Generate a CsvPath statement")

        self.run_button = QPushButton()
        self.run_button.setText("Generate")
        self.run_button.clicked.connect(self.do_generate)
        self.cancel_button = QPushButton()
        self.cancel_button.setText("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        self.save_button = QPushButton()
        self.save_button.setText("Save")
        self.save_button.setEnabled(False)
        self.save_button.clicked.connect(self.on_save)
        #
        # self.saved is a requirement for using CsvPathTextEdit. that class
        # expects its parent to have a self.saved. we don't need one otherwise.
        #
        self.saved = None
        #
        #
        #
        self.setFixedHeight(350)
        self.setFixedWidth(650)
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        self.form_layout = QFormLayout()
        self.form_layout.setRowWrapPolicy(QFormLayout.RowWrapPolicy.DontWrapRows)
        main_layout.addLayout(self.form_layout)

        #
        # show csv data path
        #
        self.data_path = QScrollArea()
        self.data_path.setWidgetResizable(True)
        self.data_path.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.data_path.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.data_path.setFixedHeight(33)

        self.data_path_text = QLabel()
        self.data_path_text.setText(self.path)
        self.data_path_text.setTextInteractionFlags(Qt.TextSelectableByMouse)

        self.data_path.setWidget(self.data_path_text)
        self.form_layout.addRow("Sample data: ", self.data_path)

        #
        # show number of rows
        #
        self.sample_size = QComboBox()
        self.sample_size.setEditable(False)
        self.sample_size.setFixedWidth(55)
        for _ in [10,50,100]:
            self.sample_size.addItem(str(_))
        self.sample_size.editTextChanged.connect(self.on_sample_size_change)
        box = HelpIconPackager.add_help(
            main=self.main,
            widget=self.sample_size,
            on_help=self.on_help_sample_size
        )
        self.form_layout.addRow("Sample size: ", box)
        #
        # instructions to the AI
        #
        self.instructions = QPlainTextEdit()
        self.instructions.textChanged.connect(self.on_instructions_changed)

        box = HelpIconPackager.add_help(
            main=self.main,
            widget=self.instructions,
            on_help=self.on_help_instructions
        )
        self.form_layout.addRow("AI instructions: ", box)

        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(self.cancel_button)
        buttons_layout.addWidget(self.run_button)
        buttons_layout.addWidget(self.save_button)
        main_layout.addLayout(buttons_layout)





    def show_dialog(self) -> None:
        #
        # check config is ready?
        #
        self.exec()


    def on_sample_size_change(self) -> None:
        # enable the send button
        ...

    def on_instructions_changed(self) -> None:
        # enable the send button
        ...

    def _show_help(self, md:str) -> None:
        if md is None:
            self.main.helper.close_help()
            return
        self.main.helper.get_help_tab().setMarkdown(md)
        if not self.main.helper.is_showing_help():
            self.main.helper.on_click_help()

    def on_help_answer(self) -> None:
        md = HelpFinder(main=self.main).help("generate/answer.md")
        self._show_help(md)

    def on_help_sample_size(self) -> None:
        md = HelpFinder(main=self.main).help("generate/sample_size.md")
        self._show_help(md)

    def on_help_instructions(self) -> None:
        md = HelpFinder(main=self.main).help("generate/instructions.md")
        self._show_help(md)

    def do_generate(self) -> None:
        cc = self.main.csvpath_config
        path = os.path.dirname(cc.configpath)
        path = os.path.join(path, "generator.ini")
        print(f"generatorpath: {path}")
        config = GeneratorConfig(path)
        generator = Generator(config)
        generator.version_key="validation"
        generator.csvpath_config = cc
        generator.csvpath_logger = self.main.logger
        generator.config.dump_config_info()
        generator.tools = [
            LiteLLMRunTool().tool_definition(),
            LiteLLMFunctionTool().tool_definition()
        ]
        context = generator.config.get("version", "context")
        context = generator.context_manager.get_context(context)
        prompt = generator.prompt_manager.create_prompt()

        n = self.sample_size.currentText()
        n = int(n)
        lines = []
        print(f"getting nomorethan {n} lines sample from {self.path}")
        with DataFileReader(self.path) as r:
            for i, _ in enumerate(r.source):
                _ = _.strip()
                if _ == "":
                    continue
                lines.append(_)
                if i > n:
                    break

        data = "\n".join(lines)
        prompt.example = data
        prompt.rules = self.instructions.toPlainText()
        if prompt.rules is None:
            prompt.rules = ""

        prompt.save()
        generation = generator.do_send(context=context, prompt=prompt, datapath=self.path)
        text = generation.response_text

        if not hasattr( self, "answer"):
            self.answer = ClassLoader.load(
                "from flightpath.widgets.csvpath_text_edit import CsvPathTextEdit",
                args=[],
                kwargs={"main":self.main, "parent":self, "editable":EditStates.EDITABLE}
            )
            self.answer.setLineWrapMode(QPlainTextEdit.NoWrap)
            self.answer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            addbox = True
            box = HelpIconPackager.add_help(
                main=self.main,
                widget=self.answer,
                on_help=self.on_help_answer
            )
            self.form_layout.addRow("Answer: ", box)

        self.answer.setPlainText(text)
        CsvPathSyntaxHighlighter(self.answer.document())
        self.save_button.setEnabled(True)






    def on_save(self) -> None:
        text = self.answer.toPlainText()
        if text is None or str(text).strip() == "":
            return
        self._save_to_file(text)

    def _save_to_file(self, text:str) -> None:
        dialog = QInputDialog()
        dialog.setFixedSize(QSize(420, 125))
        dialog.setLabelText("Save results to file: ")
        ok = dialog.exec()
        new_name = dialog.textValue()
        if ok and new_name:
            thedir = os.path.dirname(self.path)
            if not new_name.endswith(".csvpath") and not new_name.endswith(".csvpaths"):
                new_name += ".csvpaths"

            path = fiut.deconflicted_path( thedir, new_name )
            with DataFileWriter(path=path) as file:
                file.write(text)
        self.close()

















