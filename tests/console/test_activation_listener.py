"""
Unit tests for FileActivationListener threading and activation behaviour.

Background
----------
csvpath 0.0.615 fixed two bugs in FileActivationListener:

1. Thread-safety / segfault fix
   metadata_update() now creates self.my_csvpaths = CsvPaths() on the calling
   thread BEFORE calling self.start().  Previously CsvPaths() was created inside
   _metadata_update(), which runs on the background thread, causing Lark grammar
   initialisation to race Qt's event-loop (GIL contention with filterAcceptsRow()
   → segfault in Thread 0).

2. Reference-correctness fix
   _metadata_update() now passes mdata.named_file_ref (the full
   "$name.files.<fingerprint>" reference) to activate_if() instead of the plain
   mdata.named_file_name.  FileManager.get_named_file_uuid() was also updated to
   accept $name.files.xxx references, so the specific arriving registration is
   activated rather than an arbitrary version resolved by name alone.

Run with:
  QT_QPA_PLATFORM=offscreen poetry run python -m pytest tests/console/test_activation_listener.py -v
"""

import pytest
from unittest.mock import MagicMock, patch

from csvpath.managers.files.files_activation_listener import FileActivationListener


def _make_mdata(*, named_file_name: str, named_file_ref: str) -> MagicMock:
    mdata = MagicMock()
    mdata.named_file_name = named_file_name
    mdata.named_file_ref = named_file_ref
    return mdata


# ---------------------------------------------------------------------------
# _metadata_update tests
# ---------------------------------------------------------------------------


def test_metadata_update_passes_full_ref_to_activate_if():
    """
    _metadata_update() must call activate_if() with the full mdata.named_file_ref
    (e.g. "$my-file.files.abc123fingerprint"), not the plain named_file_name.

    The full reference carries the fingerprint of the specific registration that
    arrived.  Passing only the name would activate against an arbitrary version
    resolved by name rather than the one that triggered the event.
    """
    mdata = _make_mdata(
        named_file_name="my-file",
        named_file_ref="$my-file.files.abc123fingerprint",
    )

    activate_calls = []
    mock_csvpaths = MagicMock()
    mock_csvpaths.file_manager.activator.activate_if = lambda ref: activate_calls.append(ref)

    listener = object.__new__(FileActivationListener)
    listener.my_csvpaths = mock_csvpaths

    listener._metadata_update(mdata)

    assert len(activate_calls) == 1, (
        "_metadata_update() must call activate_if() exactly once"
    )
    assert activate_calls[0] == "$my-file.files.abc123fingerprint", (
        f"activate_if() must receive the full named_file_ref; got: {activate_calls[0]!r}"
    )


def test_metadata_update_does_not_create_csvpaths_internally():
    """
    _metadata_update() must use self.my_csvpaths and must not create a new
    CsvPaths() instance internally.

    Creating CsvPaths() inside the background thread was the root cause of the
    segfault: Lark grammar initialisation raced Qt's event-loop on the main thread.
    The fix moves CsvPaths() construction to metadata_update(), which runs on the
    calling (main) thread before self.start() is called.
    """
    mdata = _make_mdata(
        named_file_name="sales-data",
        named_file_ref="$sales-data.files.deadbeef0123",
    )

    listener = object.__new__(FileActivationListener)
    listener.my_csvpaths = MagicMock()

    with patch(
        "csvpath.managers.files.files_activation_listener.CsvPaths"
    ) as mock_cls:
        listener._metadata_update(mdata)

    mock_cls.assert_not_called()


# ---------------------------------------------------------------------------
# run() tests
# ---------------------------------------------------------------------------


def test_run_calls_wrap_up_on_my_csvpaths():
    """
    run() must call self.my_csvpaths.wrap_up() after _metadata_update() returns.

    wrap_up() releases resources held by the CsvPaths instance created in
    metadata_update().  It is called by run(), not by _metadata_update() itself,
    so self.my_csvpaths must be set before the thread starts.
    """
    mdata = _make_mdata(named_file_name="any-file", named_file_ref="$any-file.files.abc")
    listener = object.__new__(FileActivationListener)
    listener.my_csvpaths = MagicMock()
    listener.metadata = mdata

    with patch.object(listener, "_metadata_update"):
        listener.run()

    listener.my_csvpaths.wrap_up.assert_called_once_with()


def test_run_completes_without_error_when_my_csvpaths_is_set():
    """
    run() must complete without raising when self.my_csvpaths is properly
    initialised by metadata_update() before self.start() is called.

    Previously run() called self.csvpaths.wrap_up() but self.csvpaths was
    never set, raising AttributeError.  The fix renames the attribute to
    self.my_csvpaths and assigns it in metadata_update() before start().
    """
    mdata = _make_mdata(named_file_name="any", named_file_ref="$any.files.abc")
    listener = object.__new__(FileActivationListener)
    listener.my_csvpaths = MagicMock()
    listener.metadata = mdata

    listener.run()  # must not raise

    listener.my_csvpaths.wrap_up.assert_called_once_with()


# ---------------------------------------------------------------------------
# metadata_update() thread-spawn and thread-safety tests
# ---------------------------------------------------------------------------


def test_metadata_update_stores_mdata_on_self():
    """
    metadata_update() must store mdata on self.metadata before starting the
    thread so run() can access it via self.metadata.
    """
    mdata = _make_mdata(named_file_name="my-file", named_file_ref="$my-file.files.abc")
    listener = object.__new__(FileActivationListener)

    csvpath_target = "csvpath.managers.files.files_activation_listener.CsvPaths"
    with patch(csvpath_target), patch.object(listener, "start"):
        listener.metadata_update(mdata)

    assert listener.metadata is mdata, (
        "metadata_update() must store mdata on self.metadata so run() can access it"
    )


def test_metadata_update_creates_my_csvpaths_before_starting_thread():
    """
    metadata_update() must create self.my_csvpaths = CsvPaths() BEFORE calling
    self.start().  This is the core fix for the segfault: Lark grammar
    initialisation happens on the calling thread, not in the background thread,
    so there is no GIL contention with Qt's event-loop.
    """
    mdata = _make_mdata(named_file_name="my-file", named_file_ref="$my-file.files.abc")
    listener = object.__new__(FileActivationListener)

    order = []
    mock_csvpaths = MagicMock()

    csvpath_target = "csvpath.managers.files.files_activation_listener.CsvPaths"
    with patch(csvpath_target, side_effect=lambda: (order.append("csvpaths_created"), mock_csvpaths)[1]):
        with patch.object(listener, "start", side_effect=lambda: order.append("start_called")):
            listener.metadata_update(mdata)

    assert order == ["csvpaths_created", "start_called"], (
        "CsvPaths() must be constructed before start() is called — "
        f"actual order: {order}"
    )
    assert listener.my_csvpaths is mock_csvpaths, (
        "metadata_update() must store the CsvPaths instance on self.my_csvpaths"
    )


def test_metadata_update_calls_thread_start():
    """
    metadata_update() calls self.start() — this spawns a raw threading.Thread
    that runs _metadata_update() concurrently with Qt's main event loop.

    start() is mocked here to prevent the thread from actually running; the
    assertion confirms the spawn is attempted.  The segfault fix ensures that
    by the time start() is called, Lark grammar initialisation is already
    complete on the calling thread.
    """
    mdata = _make_mdata(named_file_name="my-file", named_file_ref="$my-file.files.abc")
    listener = object.__new__(FileActivationListener)

    csvpath_target = "csvpath.managers.files.files_activation_listener.CsvPaths"
    with patch(csvpath_target):
        with patch.object(listener, "start") as mock_start:
            listener.metadata_update(mdata)

    mock_start.assert_called_once_with()
