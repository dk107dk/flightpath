import os
import jsonpickle
import tempfile

from PySide6.QtWidgets import ( # pylint: disable=E0611
        QVBoxLayout,
        QHBoxLayout,
        QPushButton,
        QLabel,
        QDialog,
        QFormLayout,
        QComboBox,
        QInputDialog,
        QSizePolicy,
        QScrollArea,
        QTabWidget,
        QWidget,
        QCheckBox,
        QApplication,
        QPlainTextEdit,
        QMessageBox
)
from PySide6.QtCore import Qt, QSize

from csvpath.util.file_readers import DataFileReader
from csvpath.util.file_writers import DataFileWriter

from flightpath_generator.util.config import Config as GeneratorConfig
from flightpath_generator import Generator
from flightpath_generator.prompts import Generation

from flightpath.editable import EditStates
from flightpath.widgets.panels.data_viewer import DataViewer
from flightpath.widgets.panels.table_model import TableModel

from flightpath.widgets.help.plus_help import HelpIconPackager
from flightpath.util.help_finder import HelpFinder
from flightpath.util.file_utility import FileUtility as fiut

class GenerateCsvDialog(QDialog):


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

        self.setWindowTitle("Generate sample CSV data")

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
        #
        #
        self.setMinimumHeight(153)
        self.setMinimumWidth(650)
        self.setSizeGripEnabled(True)


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
        self.form_layout.addRow("Generating from: ", self.data_path)


        #
        # show number of rows
        #
        self.sample_size = QComboBox()
        self.sample_size.setFixedHeight(31)
        self.sample_size.setEditable(False)
        self.sample_size.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        for _ in [50,100,250,500,1000]:
            self.sample_size.addItem(str(_))
        self.sample_size.editTextChanged.connect(self.on_sample_size_change)
        box = HelpIconPackager.add_help(
            main=self.main,
            widget=self.sample_size,
            on_help=self.on_help_generate_data_size
        )
        self.form_layout.addRow("Sample size: ", box)
        label = self.form_layout.labelForField(box)
        label.setFixedHeight(33)


        self.show_instructions = QCheckBox("")
        self.show_instructions.setChecked(False)
        self.show_instructions.stateChanged.connect(self._show_instructions)
        self.form_layout.addRow("Provide instructions: ", self.show_instructions)

        self.instructions = QPlainTextEdit()
        self.instructions.textChanged.connect(self.on_instructions_changed)
        self.instructions_box = HelpIconPackager.add_help(
            main=self.main,
            widget=self.instructions,
            on_help=self.on_help_instructions
        )
        #self.form_layout.addRow("Instructions: ", self.instructions_box)

        self.tabs = QTabWidget(parent=self)
        self.box = HelpIconPackager.add_help(
            main=self.main,
            widget=self.instructions,
            on_help=self.on_help_instructions
        )
        self.tabs.addTab(self.box, "Instructions")
        self.form_layout.addRow("  ", self.tabs)
        self.manifests = None
        self._show_instructions()


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

    def on_help_instructions(self) -> None:
        md = HelpFinder(main=self.main).help("generate/csv_instructions.md")
        self.on_help(md)

    def on_help_generate_data_size(self) -> None:
        md = HelpFinder(main=self.main).help("generate/generate_data_size.md")
        self.on_help(md)

    def on_help(self, md:str) -> None:
        if md is None:
            self.main.helper.close_help()
            return
        self.main.helper.get_help_tab().setMarkdown(md)
        if not self.main.helper.is_showing_help():
            self.main.helper.on_click_help()

    def _show_instructions(self) -> None:
        label = self.form_layout.labelForField(self.tabs)
        if label is None:
            raise ValueError("Tabs label cannot be None")
        if self.show_instructions.isChecked():
            label.show()
            self.tabs.show()
            self.resize(self.sizeHint())
        else:
            label.hide()
            self.tabs.hide()
            self.resize(650, 153)

    def get_generator(self) -> Generator:
        cc = self.main.csvpath_config
        path = os.path.dirname(cc.configpath)
        path = os.path.join(path, "generator.ini")
        print(f"generatorpath: {path}")
        config = GeneratorConfig(cfg=cc, configpath=path)
        generator = Generator(config)
        generator.version_key="testdata"
        generator.csvpath_config = cc
        generator.csvpath_logger = self.main.logger
        generator.config.dump_config_info()
        return generator

    def do_generate(self) -> None:
        self.run_button.setEnabled(False)
        QApplication.processEvents()   # refresh UI since you're on main thread
        generator = self.get_generator()
        context = generator.config.get("version", "context")
        context = generator.context_manager.get_context(context)
        prompt = generator.prompt_manager.create_prompt()
        inst = self.instructions.toPlainText()
        if inst is None:
            inst = ""
        inst = inst.strip()
        if inst != "":
            inst = f"Adhere to the following instructions as you create your test data: {inst}"
        n = self.sample_size.currentText()
        with DataFileReader(self.path) as file:
            data = file.source.read()
            values = {"example":data, "number_of_lines":n, "instructions":inst}
            prompt.example_values = values
        prompt.save()
        generation = None
        if True:
            generation = generator.do_send(context=context, prompt=prompt, datapath=self.path)
        self.process_generations(generation)
        self.process_data(generation)
        self.save_button.setEnabled(True)
        QApplication.processEvents()   # refresh UI since you're on main thread

    def process_data(self, generation:Generation) -> None:
        text = generation.response_text
        if text is None:
            return
        text = text.strip()
        if text == "":
            return
        print(f"generatedtext: {text}")
        if text and text.strip().find(","):
            with tempfile.NamedTemporaryFile(mode='w+t', delete=False, suffix='.csv') as file:
                file.write(text)
                file.flush()
                data = []
                with DataFileReader( file.name, encoding="utf-8" ) as datafile:
                    for line in datafile.next():
                        data.append(line)
                print(f"csldfv: data: {data}")
                table_model = TableModel(data=data, editable=EditStates.UNEDITABLE)
                #
                # in this case, self.main is the QSplitter. that's hard to correct, atm.
                #
                print(f"csldfv: main: {self.main}")
                path = self.main.selected_file_path
                path = path[0:path.rfind(".")]
                path = f"{path}.csv"
                print(f"csldfv: path: {path}")
                data_view = DataViewer(parent=self.main, editable=EditStates.UNEDITABLE, path=path)
                #
                # exp: this is an important patch.
                #
                data_view.main = self.main

                data_view.setObjectName("results")
                self.tabs.addTab(data_view, "Results")
                data_view.display_data(table_model)
                self.tabs.setCurrentIndex(2)


    def process_generations(self, generation:Generation) -> None:
        if generation is None:
            raise ValueError("Generation cannot be None")
        self.manifests = QPlainTextEdit()
        self.tabs.addTab(self.manifests, "Report")
        self.tabs.setCurrentIndex(1)
        i = 1
        gs = generation.generator.generations
        i += len(gs)
        turns = generation.generator.get_turns(text_list=False)
        js = jsonpickle.encode(turns, unpicklable=False, indent=2)
        self.manifests.setPlainText(js)


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
            if not new_name.endswith(".csv"):
                new_name += ".csv"

            path = fiut.deconflicted_path( thedir, new_name )
            with DataFileWriter(path=path) as file:
                file.write(text)
        #self.close()
        self.cancel_button.setText("Close")
        self.save_button.setEnabled(False)
        QApplication.processEvents()   # refresh UI since you're on main thread











