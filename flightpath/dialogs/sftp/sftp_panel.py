from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QTreeWidget,
    QTreeWidgetItem,
    QTreeWidgetItemIterator,
)

from csvpath.managers.server_config import ServerConfig
from flightpath.dialogs.sftp.sftp_form import SftpForm

from flightpath.util.style_utils import StyleUtility as stut


class SftpPanel(QWidget):
    TREE_STYLE = """
            QTreeWidget {
                border: 1px solid #d0d0d0;
                margin: 0px;
                padding-left: 1px;
            }
            QTreeWidget::item:hover {
              color: #FFF;
              background: black;
            }
            QTreeWidget::item:selected {
              color: #FFF;
              background: gray;
            }
            """

    def __init__(self, *, main, parent, configs: dict[str, ServerConfig]):
        super().__init__(parent)
        self.main = main
        self.my_parent = parent

        self.configs = configs if configs is not None else {}
        #
        # style stuff
        #
        self.setAttribute(Qt.WA_StyledBackground, True)
        stut.set_common_style(self)
        #
        # Sidebar menu
        self._tree = None
        #
        # set up the forms
        #
        self.form = None
        self.setup_form()
        #
        #
        #
        self.h_layout = QHBoxLayout()
        self.h_layout.addWidget(self.tree)
        self.h_layout.addWidget(self.form)
        self.setLayout(self.h_layout)

    @property
    def configs(self) -> dict:
        return self._configs

    @configs.setter
    def configs(self, cs: dict) -> None:
        self._configs = cs

    def clear_form(self) -> None:
        self.form.name.setText("")
        self.form.server.setText("")
        self.form.port.setText("")
        self.form.username.setText("")
        self.form.password.setText("")

    def update_form(self, name: str) -> None:
        print(f"panel: update form: {name}")
        self.form.name.setText(name)
        config = self._config_for_name(name)
        self.form.server.setText(config.address)
        if config.port:
            n = str(config.port)
        else:
            n = "22"
        self.form.port.setText(n)
        self.form.username.setText(config.username)
        self.form.password.setText(config.password)

    def remove_server(self, name: str) -> None:
        print(f"panel: remove_server: {name}")
        if name in self.configs:
            del self.configs[name]
            item = self.item_for_name(name)
            # parent = item.parent()
            parent = self._tree.invisibleRootItem()
            print(f"remove server: parent: {parent}")
            parent.removeChild(item)
            #
            # clear the form
            #
            item = self._tree.topLevelItem(0)
            print(f"remove server: selected next: {item.text(0)}")
            if item:
                self._tree.setCurrentItem(item)
                print("remove server: setting up form")
                self.setup_form()
                print("remove server: done removeing and setting up form")
            else:
                print("remove server: no next item, clearing form")
                self.clear_form()
        else:
            print(f"panel: remove_server: {name} not found")
        self.my_parent.set_button.setEnbled(True)

    def item_for_name(self, name: str):
        iterator = QTreeWidgetItemIterator(self._tree)
        while iterator.value():
            item = iterator.value()
            if item.text(0) == name:
                return item
            iterator += 1
        return None

    def update_server(self, name: str = None) -> None:
        #
        # add or update a config
        #
        name = self.form.name.text() if name is None else name
        #
        # find a config, if exists
        #
        config = self._config_for_name(name)
        if config is None:
            config = ServerConfig()
            #
            # create config and add to tree
            #
            self.configs[name] = config
        #
        # put values in config
        #
        config.address = self.form.server.text()
        n = 22
        try:
            n = int(self.form.port.text()) if str(n).strip() != "" else n
        except Exception:
            ...
        config.port = n
        config.username = self.form.username.text()
        config.password = self.form.password.text()
        #
        # find tree item
        #
        iterator = QTreeWidgetItemIterator(self._tree)
        while iterator.value():
            item = iterator.value()
            if item.text(0) == name:
                self._tree.setCurrentItem(item)
                self.my_parent.set_button.setEnabled(True)
                return
            iterator += 1
        item = QTreeWidgetItem(self._tree)
        item.setText(0, name)
        self._tree.setCurrentItem(item)
        self.my_parent.set_button.setEnabled(True)

    def _config_for_name(self, name: str):
        if self.configs is None:
            return None
        return self.configs.get(name)

    def _top_item(self):
        if self.tree is None:
            return None
        return self.tree.topLevelItem(0)

    def setup_form(self) -> None:
        print("panel: setup form")
        if self.form is None:
            self.form = SftpForm(parent=self, main=self.main)
        print(f"panel: setup form: form: {self.form}, configs: {self.configs}")
        if self.configs is None:
            return
        item = self._top_item()
        print(f"panel: setup form: top item: {item}")
        #
        # populate the form with the top config name
        #
        if item is None:
            return
        name = item.text(0)
        print(f"panel: setup form: top item name: {name}")
        config = self._config_for_name(name)
        print(f"panel: setup form: top item config for name {name} is: {config}")
        if config is None:
            # this shouldn't happen
            return
        print(f"panel: setup form: doing setup of {name}")
        self.form.name.setText(name)
        print(f"panel: setup form: doing setup of {config.address}")
        self.form.server.setText(config.address)
        print(f"panel: setup form: doing setup of {self.form.server.text()}")
        print(f"panel: setup form: doing setup of {config.port}")
        self.form.port.setText(str(config.port))
        print(f"panel: setup form: doing setup of {config.username}")
        self.form.username.setText(config.username)
        print(f"panel: setup form: doing setup of {config.password}")
        self.form.password.setText(config.password)

    # deleteme
    # def switch_form(self, index: QModelIndex):
    #   name = index.data()
    # find the sftp config for name
    # and populate the form

    def _setup_tree(self) -> None:
        tree = QTreeWidget()
        tree.setColumnCount(1)
        #
        # shouldn't need this because hidden
        #
        tree.setHeaderLabels(["Name"])
        tree.setHeaderHidden(True)
        tree.setFixedWidth(180)
        tree.setIndentation(8)
        if self.configs is not None:
            for k, _ in self.configs.items():
                item = QTreeWidgetItem(tree)
                item.setText(0, k)
        # tree.clicked.connect(self.switch_form)
        tree.setStyleSheet(self.TREE_STYLE)
        self._tree = tree
        if self.configs and len(self.configs) > 0:
            item = self._tree.topLevelItem(0)
            self._tree.setCurrentItem(item)
        self._tree.itemClicked.connect(self.on_item_clicked)

    def on_item_clicked(self, item, column):
        print(f"panel: on_item_clicked: item: {item}, col: {column}")
        name = item.text(0)
        print(f"panel: on_item_clicked: name: {name}")
        self.update_form(name)
        print("panel: on_item_clicked: done")

    @property
    def tree(self) -> QTreeWidget:
        if self._tree is None:
            self._setup_tree()
        return self._tree
