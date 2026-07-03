import pytest

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
    return win
