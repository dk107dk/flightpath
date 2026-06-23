import gc
import logging
from logging import Logger

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
def csvpath_logging_cleanup():
    """
    Prevents CsvPath FileHandlers from accumulating on global Python loggers
    across tests, which can stall logging.shutdown() in later tests.

    Root cause: LogUtility.config_logger() in CsvPath Framework modifies
    logger.handlers while iterating it (calls logger.removeHandler() inside
    a for-loop over logger.handlers).  Removing the first handler shifts the
    list, so the second handler is skipped every time.  Over a test suite of
    200+ runs, hundreds of open FileHandlers pile up on global logger objects.
    When run_paths() calls lout.rotate_log() -> logging.shutdown() before each
    new run, Python has to flush and close all of those stale handles, which
    is slow enough on some machines to exceed the 20-second waitUntil timeout.

    This fixture runs after every test and closes + detaches all FileHandlers
    from every logger currently registered with Python's logging system, then
    clears the CsvPath LogUtility.LOGGERS index.  The logging system
    re-initialises cleanly for the next test.
    """
    yield
    # 1. Flush any pending Qt deferred-deletions and queued cross-thread signals
    #    so widgets and worker objects from this test are destroyed before we
    #    touch the logging system.
    app = QApplication.instance()
    if app is not None:
        app.processEvents()

    # 2. Clear the CsvPath LogUtility.LOGGERS index so stale logger names
    #    from this test's CsvPaths instances don't accumulate.
    try:
        from csvpath.util.log_utility import LogUtility as clout
        clout.LOGGERS.clear()
    except Exception:
        pass

    # 3. Close and detach all FileHandlers from every registered Python logger.
    #    LogUtility.config_logger() has a list-mutation bug that leaves the
    #    second handler unclosed whenever a logger has 2+ handlers; this sweeps
    #    up anything that slipped through.
    with logging._lock:
        names = list(Logger.manager.loggerDict.keys())

    for name in names:
        try:
            entry = Logger.manager.loggerDict.get(name)
            if not isinstance(entry, logging.Logger):
                continue
            for handler in entry.handlers[:]:
                if isinstance(handler, logging.FileHandler):
                    try:
                        handler.flush()
                        handler.close()
                    except Exception:
                        pass
                    entry.removeHandler(handler)
        except Exception:
            pass

    # 4. Force GC so handler objects are actually destroyed and their weakrefs
    #    in logging._handlerList go dead.  Without this, logging.shutdown()
    #    called from lout.rotate_log in the next run_paths() still sees live
    #    (but closed) handlers and flushes them all — which is slow.
    gc.collect()


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
