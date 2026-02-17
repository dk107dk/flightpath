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
from flightpath.widgets.help.plus_help import HelpIconPackager
from flightpath.util.help_finder import HelpFinder
from flightpath.util.file_utility import FileUtility as fiut
from flightpath.util.syntax.csvpath_highlighter import CsvPathSyntaxHighlighter
from flightpath.editable import EditStates

from flightpath_generator.client.run_tool import LiteLLMRunTool
#from flightpath_generator.client.syntax_tool import LiteLLMSyntaxTool
from flightpath_generator.client.function_tool import LiteLLMFunctionTool

class AskQuestionDialog(QDialog):


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

        self.setWindowTitle("Ask a CsvPath question")

        self.run_button = QPushButton()
        self.run_button.setText("Answer")
        self.run_button.clicked.connect(self.do_generate)
        self.cancel_button = QPushButton()
        self.cancel_button.setText("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        self.save_button = QPushButton()
        self.save_button.setText("Save")
        self.save_button.setEnabled(False)
        self.save_button.clicked.connect(self.on_save)

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
        # show csvpath path
        #
        self.csvpath_path = QScrollArea()
        self.csvpath_path.setWidgetResizable(True)
        self.csvpath_path.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.csvpath_path.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.csvpath_path.setFixedHeight(33)

        self.csvpath_path_text = QLabel()
        self.csvpath_path_text.setText(self.path)
        self.csvpath_path_text.setTextInteractionFlags(Qt.TextSelectableByMouse)

        self.csvpath_path.setWidget(self.csvpath_path_text)
        self.form_layout.addRow("Current file: ", self.csvpath_path)

        #
        # show csv data path
        #
        data = self._get_data_path()
        self.data_path = QScrollArea()
        self.data_path.setWidgetResizable(True)
        self.data_path.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.data_path.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.data_path.setFixedHeight(33)

        self.data_path_text = QLabel()
        path = self._get_data_path()
        if path is not None:
            self.data_path_text.setText(path)

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

        self.question = QPlainTextEdit()
        self.question.textChanged.connect(self.on_question_changed)

        box = HelpIconPackager.add_help(
            main=self.main,
            widget=self.question,
            on_help=self.on_help_question
        )
        self.form_layout.addRow("Question: ", box)

        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(self.cancel_button)
        buttons_layout.addWidget(self.run_button)
        buttons_layout.addWidget(self.save_button)
        main_layout.addLayout(buttons_layout)


    def _get_data_path(self) -> str:
        print(f"ask: _get_data_path")
        csvpath = None
        with DataFileReader(self.path) as file:
            csvpath = file.read()
        print(f"ask: _get_data_path: csvpath: {csvpath}")
        stmt = None
        c = None
        for _ in csvpath.split("---- CSVPATH ----"):
            if _.find("test-data:") > -1:
                stmt, c = self.parent.parent._statement_and_comment(_)
                break
        print(f"ask: _get_data_path: stmt: {stmt}")
        if stmt is None:
            return None
        path = self.parent.parent._get_filepath(stmt, c)
        print(f"ask: _get_data_path: path: {path}")
        return path


    def show_dialog(self) -> None:
        #
        # check config is ready?
        #
        self.exec()


    def on_sample_size_change(self) -> None:
        # enable the send button
        ...

    def on_question_changed(self) -> None:
        # enable the send button
        ...

    def _show_help(self, md:str) -> None:
        if md is None:
            self.main.helper.close_help()
            return
        self.main.helper.get_help_tab().setMarkdown(md)
        if not self.main.helper.is_showing_help():
            self.main.helper.on_click_help()

    def on_help_question(self) -> None:
        md = HelpFinder(main=self.main).help("generate/question.md")
        self._show_help(md)

    def on_help_answer(self) -> None:
        md = HelpFinder(main=self.main).help("generate/answer.md")
        self._show_help(md)

    def on_help_test_data(self) -> None:
        md = HelpFinder(main=self.main).help("generate/test_data.md")
        self._show_help(md)

    def on_help_sample_size(self) -> None:
        md = HelpFinder(main=self.main).help("generate/sample_size.md")
        self._show_help(md)

    def do_generate(self) -> None:
        cc = self.main.csvpath_config
        path = os.path.dirname(cc.configpath)
        path = os.path.join(path, "generator.ini")
        print(f"generatorpath: {path}")
        config = GeneratorConfig(path)
        generator = Generator(config)
        generator.version_key="question"
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

        data_path = self.data_path_text.text()
        print(f"getting nomorethan {n} lines sample from {data_path}")
        with DataFileReader(data_path) as r:
            for i, _ in enumerate(r.source):
                _ = _.strip()
                if _ == "":
                    continue
                lines.append(_)
                if i > n:
                    break

        data = "\n".join(lines)
        prompt.example = data
        prompt.rules = self.question.toPlainText()

        #print(f"promte: {prompt.to_json()}")

        prompt.save()
        generator.tools = [ LiteLLMRunTool().tool_definition() ]
        generation = None
        try:
            generation = generator.do_send(context=context, prompt=prompt, datapath=data_path)
        except Exception as ex:
            print(f"Error: {ex}")
            ...
        if generation is None:
            text = f"Cannot ask a question. Is your config set correctly?"
        else:
            text = generation.response_text
        print(f"generatedtext: {text}")

        if not hasattr( self, "answer"):
            self.answer = ClassLoader.load(
                "from flightpath.widgets.csvpath_text_edit import CsvPathTextEdit",
                args=[],
                kwargs={"main":self.main, "parent":self.parent, "editable":EditStates.EDITABLE}
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

















