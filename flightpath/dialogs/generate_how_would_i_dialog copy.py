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
from flightpath_generator.util.config import Config as GeneratorConfig
from flightpath_generator import Generator
from flightpath_generator.client.run_tool import LiteLLMRunTool
#from flightpath_generator.client.syntax_tool import LiteLLMSyntaxTool
from flightpath_generator.client.function_tool import LiteLLMFunctionTool
from flightpath.widgets.help.plus_help import HelpIconPackager
from flightpath.util.help_finder import HelpFinder
from flightpath.util.file_utility import FileUtility as fiut

class GenerateHowWouldIDialog(QDialog):


    def __init__(self, *, main, path):
        super().__init__(main)
        if path is None:
            raise ValueError("Path cannot be None")
        if main is None:
            raise ValueError("Main cannot be None")

        self.main = main
        self.path = path


        self.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint)
        self.setWindowModality(Qt.NonModal)

        self.setWindowTitle("Generate a CsvPath statement")

        self.run_button = QPushButton()
        self.run_button.setText("Generate")
        self.run_button.clicked.connect(self.do_generate)
        self.cancel_button = QPushButton()
        self.cancel_button.setText("Cancel")
        self.cancel_button.clicked.connect(self.reject)

        #
        #
        #
        self.setFixedHeight(200)
        self.setFixedWidth(650)
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)
        #
        # show csv data path
        #
        self.data_path = QScrollArea()
        self.data_path.setWidgetResizable(True)
        self.data_path.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.data_path.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.data_path.setFixedHeight(33)
        #self.data_path.setFixedWidth(384)

        self.data_path_text = QLabel()
        self.data_path_text.setText(self.path)
        self.data_path_text.setTextInteractionFlags(Qt.TextSelectableByMouse)

        self.data_path.setWidget(self.data_path_text)



        main_layout.addWidget(self.data_path)


        form_layout = QFormLayout()
        form_layout.setRowWrapPolicy(QFormLayout.RowWrapPolicy.DontWrapRows)
        main_layout.addLayout(form_layout)

        #
        # show number of rows
        #
        self.sample_size = QComboBox()
        self.sample_size.setEditable(False)
        self.sample_size.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        for _ in [50,100,250,500,1000]:
            self.sample_size.addItem(str(_))
        self.sample_size.editTextChanged.connect(self.on_sample_size_change)
        box = HelpIconPackager.add_help(
            main=self.main,
            widget=self.sample_size,
            on_help=self.on_help_sample_size
        )
        form_layout.addRow("Sample size: ", box)
        #
        # instructions to the AI
        #
        self.instructions = QPlainTextEdit()
        #self.instructions.setEditable(True)
        self.instructions.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.instructions.textChanged.connect(self.on_instructions_changed)

        box = HelpIconPackager.add_help(
            main=self.main,
            widget=self.instructions,
            on_help=self.on_help_instructions
        )
        form_layout.addRow("AI instructions: ", box)

        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(self.cancel_button)
        buttons_layout.addWidget(self.run_button)
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
        md = HelpFinder(main=self.main).help("generate/sample_size.md")
        if md is None:
            self.sidebar.main.helper.close_help()
            return
        self.main.helper.get_help_tab().setMarkdown(md)
        if not self.main.helper.is_showing_help():
            self.main.helper.on_click_help()

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
        generator.csvpath_config = cc
        generator.csvpath_logger = self.main.logger
        generator.tools = [
            LiteLLMRunTool().tool_definition(),
            LiteLLMFunctionTool().tool_definition()
        ]
        generator.config.dump_config_info()
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
        prompt.example = "Use this example data to generate your CsvPath:\n{data}"
        prompt.rules = self.instructions.toPlainText()

        print(f"promte: {prompt.to_json()}")

        prompt.save()
        generation = generator.do_send(context=context, prompt=prompt, datapath=self.path)
        text = generation.response_text
        print(f"generatedtext: {text}")

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

















