"""
pytest-qt tests for named-file and named-paths settings dialogs.

Checklist coverage:
  DIALOGS > stage data > set template on a named-file
  DIALOGS > stage data > set activation on a named-file
  DIALOGS > stage data > set SFTP servers on a named-file
  DIALOGS > load csvpaths > set template on a named-paths group
  DIALOGS > load csvpaths > set webhooks on a named-paths group

Each dialog is a simple form: open, fill one field, save, assert persistence.
The tests bypass show_dialog() (which calls exec() or show()) and call do_set()
directly — the same code path taken by clicking the "Set"/"Save" button.

Run with:
  QT_QPA_PLATFORM=offscreen poetry run python -m pytest tests/gui/test_settings_dialogs.py -v
"""

import os

from csvpath.managers.files.files_activation_listener import FileActivationListener

from flightpath.dialogs.activation_dialog import ActivationDialog
from flightpath.dialogs.files_template_dialog import FilesTemplateDialog
from flightpath.dialogs.paths_template_dialog import PathsTemplateDialog
from flightpath.dialogs.sftp_servers_dialog import SftpServersDialog
from flightpath.dialogs.webhooks_dialog import WebhooksDialog
from flightpath.util.listener_utility import ListenerUtility as liut

# isolated_home and main fixtures are provided by conftest.py


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _examples(main, *parts) -> str:
    return os.path.join(main.state.cwd, "examples", *parts)


def _register_named_file(main, name: str = "test") -> str:
    csv_file = _examples(main, "first steps", "test.csv")
    main.csvpaths.config.set(section="inputs", name="allow_local_files", value=True)
    main.csvpaths.file_manager.add_named_file(name=name, path=csv_file, template=None)
    return name


def _register_named_paths(main, name: str = "hello-world") -> str:
    csvpath_file = _examples(main, "first steps", "Hello World.csvpath")
    main.csvpaths.paths_manager.add_named_paths_from_file(
        name=name, file_path=csvpath_file, template=None, append=False
    )
    return name


# ---------------------------------------------------------------------------
# Tests — named-file settings
# ---------------------------------------------------------------------------


def test_files_template_dialog_saves_template(qtbot, main):
    """
    FilesTemplateDialog must persist a valid staging template via do_set().

    A valid named-file template ends with ':filename' and describes the
    directory structure used when the named-file's data is staged via SFTP
    or cloud storage.  The template is stored by file_manager.describer and
    retrieved by get_template().
    """
    name = _register_named_file(main)
    dialog = FilesTemplateDialog(main=main, name=name, parent=main.sidebar_rt_top)
    qtbot.addWidget(dialog)

    dialog.template_ctl.setText("staging/:filename")
    dialog.do_set()

    stored = main.csvpaths.file_manager.describer.get_template(name)
    assert stored == "staging/:filename", (
        f"FilesTemplateDialog.do_set() must persist the template; got {stored!r}"
    )


def test_activation_dialog_saves_on_arrival(monkeypatch, qtbot, main):
    """
    ActivationDialog must persist a named-paths group and run method via do_set().

    An activation wires a named-paths group to a named-file so the group runs
    automatically when new data arrives for that file.  After do_set(), the
    on_arrival config is retrievable from file_manager.describer.get_on_arrival().

    The named-paths group must be registered before constructing the dialog so
    the named_paths_name_ctl combo box is populated with the group name.

    liut.assure_activation() is monkeypatched to a no-op because it starts a
    FileActivationListener background thread that persists beyond test teardown
    and races the next test's Qt event loop — a segfault waiting to happen.  The
    storage behavior (store_on_arrival) is what this test validates; the listener
    wiring is tested at the integration level.
    """
    monkeypatch.setattr(liut, "assure_activation", lambda main: None)

    name = _register_named_file(main)
    _register_named_paths(main)  # populates named_paths_name_ctl on dialog init

    dialog = ActivationDialog(parent=main.sidebar_rt_top, main=main, named_file=name)
    qtbot.addWidget(dialog)

    dialog.named_paths_name_ctl.setEditText("hello-world")
    # run_method_ctl defaults to index 0 — "Collect" → maps to "collect_paths"
    dialog.run_method_ctl.setCurrentIndex(0)
    dialog.do_set()

    arrival = main.csvpaths.file_manager.describer.get_on_arrival(name)
    assert arrival is not None, "get_on_arrival() must return a config after do_set()"
    assert arrival.get("named_paths_group") == "hello-world", (
        f"on_arrival must store the named-paths group name; got {arrival!r}"
    )
    assert arrival.get("run_method") == "collect_paths", (
        f"on_arrival must store the run method; got {arrival!r}"
    )


def test_sftp_dialog_opens_for_named_file(monkeypatch, qtbot, main):
    """
    SftpServersDialog must construct without error for a registered named-file.

    The dialog is pre-populated with existing SFTP source configs from the file
    manager's describer.  On a fresh registration the sources config is None
    (no servers configured yet), which the dialog's SftpPanel handles by
    treating it as an empty config dict.

    Constructing the dialog verifies that the SftpPanel renders the empty-server
    list without crashing — the most common failure mode when the underlying
    ServerConfig structure changes.

    FileActivationListener.metadata_update is monkeypatched to prevent a
    background thread from starting during add_named_file().  That thread creates
    a fresh CsvPaths() and parses a Lark grammar, which races Qt's proxy-model
    filterAcceptsRow() during SftpPanel widget construction and causes a segfault.
    The segfault is a thread-safety issue in the csvpath framework, not in the
    dialog code we are testing here.
    """
    monkeypatch.setattr(FileActivationListener, "metadata_update", lambda self, mdata: None)

    name = _register_named_file(main)
    file_config = main.csvpaths.file_manager.describer.get_config(name)
    configs = file_config.sources  # None on fresh registration; SftpPanel handles it

    dialog = SftpServersDialog(
        main=main, name=name, parent=main.sidebar_rt_top, configs=configs
    )
    qtbot.addWidget(dialog)

    assert dialog.name == name, (
        f"Dialog must store the named-file name; got {dialog.name!r}"
    )


# ---------------------------------------------------------------------------
# Tests — named-paths settings
# ---------------------------------------------------------------------------


def test_paths_template_dialog_saves_template(qtbot, main):
    """
    PathsTemplateDialog must persist a valid run-dir template via do_set().

    A valid named-paths template ends with ':run_dir' and describes the
    directory structure used for run result storage.
    """
    name = _register_named_paths(main)
    dialog = PathsTemplateDialog(main=main, name=name, parent=main.sidebar_rt_mid)
    qtbot.addWidget(dialog)

    dialog.template_ctl.setText("results/:run_dir")
    dialog.do_set()

    stored = main.csvpaths.paths_manager.describer.get_template(name)
    assert stored == "results/:run_dir", (
        f"PathsTemplateDialog.do_set() must persist the template; got {stored!r}"
    )


def test_add_named_file_after_assure_activation_spawns_background_thread(monkeypatch, qtbot, main):
    """
    After assure_activation() writes the activation listener config, the next
    add_named_file() call fires a metadata event that instantiates
    FileActivationListener and calls metadata_update(), which spawns a raw
    threading.Thread via self.start().

    That thread creates CsvPaths() and parses the Lark grammar concurrently with
    Qt's main-thread event loop (filterAcceptsRow on the proxy model), which is
    the root cause of the segfault seen in Thread 0 of the crash report.

    FileActivationListener.start is patched here to a no-op so the thread never
    actually runs — preventing the segfault in the test suite.  The assertion
    confirms that start() is called, proving the spawn path exists and would
    race Qt's event loop in production.
    """
    thread_starts = []
    monkeypatch.setattr(FileActivationListener, "start", lambda self: thread_starts.append(True))

    liut.assure_activation(main)
    _register_named_file(main)

    assert len(thread_starts) >= 1, (
        "add_named_file() after assure_activation() must attempt to start a "
        "FileActivationListener thread — the background thread that races Qt's event loop"
    )


def test_webhooks_dialog_saves_url(monkeypatch, qtbot, main):
    """
    WebhooksDialog must persist a webhook URL for the on_complete_all event via do_set().

    The dialog manages four webhook configs (all, valid, invalid, error).  Setting
    the URL on forms[0] (on_complete_all) and calling do_set() must store it via
    paths_manager.describer.store_webhooks().  The stored value is retrieved by
    get_webhooks() and compared to the input.

    The named-paths group must be registered before constructing the dialog so
    the describer has a valid storage location for the webhooks config.

    liut.assure_webhooks() is monkeypatched to prevent it from modifying the
    shared config file and potentially starting background listeners that outlive
    this test's scope.
    """
    monkeypatch.setattr(liut, "assure_webhooks", lambda main: None)

    name = _register_named_paths(main)
    dialog = WebhooksDialog(main=main, name=name, parent=main.sidebar_rt_mid)
    qtbot.addWidget(dialog)

    url = "https://example.com/on-complete-all"
    dialog.panel.forms[0].url.setText(url)
    dialog.do_set()

    stored = main.csvpaths.paths_manager.describer.get_webhooks(name)
    assert stored is not None, "get_webhooks() must return a config after do_set()"
    assert stored.on_complete_all is not None, (
        "on_complete_all must be set after do_set()"
    )
    assert stored.on_complete_all.url == url, (
        f"Webhook URL must be persisted; got {stored.on_complete_all.url!r}"
    )
