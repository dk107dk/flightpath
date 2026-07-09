import pytest

from PySide6.QtWidgets import QApplication

from flightpath.util.state import State
from flightpath.main import MainWindow


@pytest.fixture(autouse=True)
def suppress_flightpath_background(monkeypatch):
    """
    Suppress the splash dialog and the pre-cache worker for all GUI tests.
    Without these, tests produce noisy FileNotFoundError tracebacks from the
    PreCacheWorker trying to read example files against the wrong cwd.
    """
    monkeypatch.setenv("FLIGHTPATH_SKIP_SPLASH", "1")
    monkeypatch.setenv("FLIGHTPATH_SKIP_PRECACHER", "1")


@pytest.fixture(autouse=True)
def flush_qt_events():
    """Flush Qt's deferred-deletion queue after every GUI test.

    Ensures that deleteLater() calls queued during a test are processed
    before the next test starts, preventing thread and object accumulation.
    """
    yield
    QApplication.processEvents()


@pytest.fixture
def isolated_home(tmp_path, monkeypatch):
    """
    State.home reads Path.home(). Without patching this, running the test
    would create real ~/FlightPath/... directories on the dev machine.
    We redirect 'home' to a tmp dir for the lifetime of the test.
    """
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    monkeypatch.setattr(State, "home", property(lambda self: str(fake_home)))
    return fake_home


@pytest.fixture
def main(qtbot, isolated_home):
    """Real MainWindow, real State, real CsvPaths — only 'home' is redirected."""
    win = MainWindow()
    qtbot.addWidget(win)
    win.show()
    qtbot.waitExposed(win)
    yield win
    # Explicitly disconnect and destroy the sidebar's model chain.
    # QFileSystemModel and DirectoryFilterProxyModel have no Qt parent so
    # they are not destroyed when the window is deleted — without this,
    # each test leaks a QFileInfoGatherer thread and both model objects.
    sidebar = getattr(win, "sidebar", None)
    if sidebar is not None:
        nav = getattr(sidebar, "file_navigator", None)
        proxy = getattr(sidebar, "proxy_model", None)
        file_model = getattr(sidebar, "file_model", None)
        if nav is not None:
            nav.setModel(None)
        if proxy is not None:
            proxy.setSourceModel(None)
            proxy.deleteLater()
        if file_model is not None:
            file_model.deleteLater()
    win.close()
    win.deleteLater()
    QApplication.processEvents()
