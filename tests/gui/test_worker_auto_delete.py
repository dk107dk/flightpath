"""
Tests that every QRunnable worker sets autoDelete=False.

Without this, Qt's thread pool auto-deletes the C++ QRunnable object from
the worker thread after run() returns.  That deletion triggers shiboken's
Python wrapper teardown, which requires the GIL.  Acquiring the GIL from
inside a Qt thread pool thread races with Python's own GIL state and causes
a segfault (QRunnableWrapper::~QRunnableWrapper / SbkDeallocWrapperCommon
visible in the crash dump).

setAutoDelete(False) hands lifecycle control back to Python's GC, which
always runs from a proper Python context.

Run with:
  QT_QPA_PLATFORM=offscreen poetry run python -m pytest tests/gui/test_worker_auto_delete.py -v
"""

import inspect
from unittest.mock import MagicMock

import pytest

from flightpath.workers.ai_worker import AiWorker
from flightpath.workers.csvpath_file_worker import CsvpathFileWorker
from flightpath.workers.general_data_worker import GeneralDataWorker
from flightpath.workers.json_data_worker import JsonDataWorker
from flightpath.workers.md_worker import MdWorker
from flightpath.workers.one_off_run import OneOffRunWorker
from flightpath.workers.precache_worker import PreCacheWorker
from flightpath.workers.run_worker import RunWorker


def _make_workers(tmp_path):
    """Instantiate every worker with minimal stubs. Returns list of (name, worker)."""
    dummy_file = str(tmp_path / "dummy.csv")
    open(dummy_file, "w").close()

    main_stub = MagicMock()

    return [
        ("AiWorker",           AiWorker(job=MagicMock())),
        ("CsvpathFileWorker",  CsvpathFileWorker(filepath=dummy_file, main=None)),
        ("GeneralDataWorker",  GeneralDataWorker(
                                   filepath=dummy_file,
                                   main=main_stub,
                                   rows="50",
                                   sampling="first_n",
                               )),
        ("JsonDataWorker",     JsonDataWorker(filepath=dummy_file, main=main_stub)),
        ("MdWorker",           MdWorker(filepath=dummy_file, main=main_stub)),
        ("OneOffRunWorker",    OneOffRunWorker(
                                   csvpath=MagicMock(),
                                   csvpath_str='$[*][print("hello")]',
                                   printer=MagicMock(),
                               )),
        ("PreCacheWorker",     PreCacheWorker(cwd=str(tmp_path), main=main_stub)),
        ("RunWorker",          RunWorker(
                                   method="collect",
                                   named_paths_name="test",
                                   named_file_name="test",
                                   template=None,
                                   csvpaths=MagicMock(),
                               )),
    ]


def test_all_workers_have_auto_delete_false(qapp, tmp_path):
    """Every worker must report autoDelete() == False to prevent GIL segfaults."""
    workers = _make_workers(tmp_path)
    failures = [name for name, w in workers if w.autoDelete()]
    assert not failures, (
        f"These workers still have autoDelete=True (segfault risk): {failures}"
    )


def test_ai_worker_auto_delete_false(qapp):
    assert not AiWorker(job=MagicMock()).autoDelete()


def test_csvpath_file_worker_auto_delete_false(qapp, tmp_path):
    f = str(tmp_path / "x.csvpath")
    open(f, "w").close()
    assert not CsvpathFileWorker(filepath=f, main=None).autoDelete()


def test_general_data_worker_auto_delete_false(qapp, tmp_path):
    f = str(tmp_path / "x.csv")
    open(f, "w").close()
    assert not GeneralDataWorker(
        filepath=f, main=MagicMock(), rows="50", sampling="first_n"
    ).autoDelete()


def test_json_data_worker_auto_delete_false(qapp, tmp_path):
    f = str(tmp_path / "x.json")
    open(f, "w").close()
    assert not JsonDataWorker(filepath=f, main=MagicMock()).autoDelete()


def test_md_worker_auto_delete_false(qapp, tmp_path):
    f = str(tmp_path / "x.md")
    open(f, "w").close()
    assert not MdWorker(filepath=f, main=MagicMock()).autoDelete()


def test_one_off_run_worker_auto_delete_false(qapp):
    assert not OneOffRunWorker(
        csvpath=MagicMock(), csvpath_str="", printer=MagicMock()
    ).autoDelete()


def test_precache_worker_auto_delete_false(qapp, tmp_path):
    assert not PreCacheWorker(cwd=str(tmp_path), main=MagicMock()).autoDelete()


def test_run_worker_auto_delete_false(qapp):
    assert not RunWorker(
        method="collect",
        named_paths_name="test",
        named_file_name="test",
        template=None,
        csvpaths=MagicMock(),
    ).autoDelete()


def test_json_data_worker_does_not_instantiate_csvpaths_in_run():
    """
    JsonDataWorker.run() must not call CsvPaths() on the thread-pool thread.

    Bug: run() called CsvPaths() to get a config object for the Box singleton
    (stale SFTP workaround). Creating a CsvPaths() instance on a background
    thread initialises the Lark grammar parser, which races with PySide's
    main-thread slot dispatch and corrupts Python reference counts, producing a
    callCppDestructor<QLineEdit> / mainThreadDeletionHandler shiboken crash.
    The csvpath library fixed the underlying SFTP issue at version 546; we are
    at 614. Fix: remove the two stale lines and their unused imports.
    """
    import flightpath.workers.json_data_worker as _mod

    assert not hasattr(_mod, "CsvPaths"), (
        "CsvPaths must not be imported in json_data_worker — shiboken crash risk"
    )
    run_source = inspect.getsource(JsonDataWorker.run)
    assert "CsvPaths()" not in run_source, (
        "JsonDataWorker.run() must not call CsvPaths() on the background thread"
    )
