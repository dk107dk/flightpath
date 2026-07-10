import os
import shutil

import pytest

from PySide6.QtWidgets import QApplication

from flightpath.util.state import State
from flightpath.main import MainWindow


_ASSETS_EXAMPLES = os.path.join(
    os.path.dirname(__file__), "..", "..", "flightpath", "assets", "examples"
)

# These three CSVs total ~5 MB. Skipping them keeps per-test disk usage low
# (~100 KB of small files instead of ~5 MB). Tests that actually need these
# files add a module-level fixture to copy just the one(s) they use.
_LARGE_EXAMPLES = {
    os.path.join("debugging", "World_Port_Index_sample.csv"),
    os.path.join("duplicates", "Alzheimers_Disease_and_Healthy_Aging_Data_sample.csv"),
    os.path.join("lookups", "Boundaries_US_Zip_Codes.csv"),
}


def copy_examples(cwd, *, also=()):
    """Copy example assets into the project's examples/ dir.

    Skips the three large CSVs by default; pass their relative paths in
    *also* to include any of them (used by module fixtures in specific files).
    """
    list_path = os.path.join(_ASSETS_EXAMPLES, "list.txt")
    examples_dir = os.path.join(cwd, "examples")
    with open(list_path) as f:
        lines = f.readlines()
    for line in lines:
        rel = line.strip()
        if not rel or rel.startswith("#"):
            continue
        if rel in _LARGE_EXAMPLES and rel not in also:
            continue
        src = os.path.join(_ASSETS_EXAMPLES, rel)
        dst = os.path.join(examples_dir, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(src, dst)


@pytest.fixture(autouse=True)
def suppress_flightpath_background(monkeypatch):
    """
    Suppress the splash dialog and the pre-cache worker for all GUI tests.
    Without these, tests produce noisy FileNotFoundError tracebacks from the
    PreCacheWorker trying to read example files against the wrong cwd.
    """
    monkeypatch.setenv("FLIGHTPATH_SKIP_SPLASH", "1")
    monkeypatch.setenv("FLIGHTPATH_SKIP_PRECACHER", "1")
    monkeypatch.setenv("FLIGHTPATH_SKIP_EXAMPLES", "1")


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
    """Real MainWindow, real State, real CsvPaths — only 'home' is redirected.

    Small example files (~100 KB total) are copied into the project after the
    window starts up. Tests that need the three large example CSVs must add
    their own module-level autouse fixture that calls copy_examples(..., also=...).
    """
    win = MainWindow()
    qtbot.addWidget(win)
    win.show()
    qtbot.waitExposed(win)
    copy_examples(win.state.cwd)
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
