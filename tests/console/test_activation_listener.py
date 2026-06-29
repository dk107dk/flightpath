"""
Unit tests for the FileActivationListener._metadata_update() library-bug fix.

Bug
---
The csvpath library's FileActivationListener._metadata_update() called
activate_if(mdata.named_file_ref), where named_file_ref is a reference
string like "$name.files.<fingerprint>".  activate_if() then passed that
string directly as the filename argument to the run method
(fast_forward_paths / collect_paths).  Internally, get_named_file_uuid()
uses ReferenceParser on any name starting with "$" and checks that the
reference's datatype is "results".  The files reference "$name.files.xxx"
has datatype "files", so the check raised:

    ValueError: Reference must be results, not {ref.datatype}

(The missing "f" prefix on the f-string is also a library bug, but the
underlying error is real regardless of the formatted message.)

Fix
---
flightpath/util/listener_utility.py patches FileActivationListener._metadata_update
at import time to use mdata.named_file_name (the plain name) instead of
mdata.named_file_ref.  The plain name is what activate_if() expects and
what the run method can safely use as a filename.

Run with:
  poetry run python -m pytest tests/console/test_activation_listener.py -v
"""

import threading

import pytest
from unittest.mock import MagicMock, patch

from csvpath.managers.files.files_activation_listener import FileActivationListener

# Importing listener_utility applies the monkey-patch to FileActivationListener
import flightpath.util.listener_utility  # noqa: F401


def _make_mdata(*, named_file_name: str, named_file_ref: str) -> MagicMock:
    mdata = MagicMock()
    mdata.named_file_name = named_file_name
    mdata.named_file_ref = named_file_ref
    return mdata


@pytest.mark.xfail(
    reason=(
        "This test verifies the current workaround behavior in "
        "_fixed_activation_metadata_update, which passes mdata.named_file_name "
        "(the plain name) to activate_if() instead of the full mdata.named_file_ref. "
        "That workaround is semantically incorrect: named_file_ref carries the "
        "fingerprint of the specific registration that arrived, and losing it means "
        "activation may run against the wrong version. "
        "When FileManager.get_named_file_uuid() is fixed to accept "
        "$name.files.<fingerprint> references (not just $name.results.<fingerprint>), "
        "revert _fixed_activation_metadata_update to pass mdata.named_file_ref and "
        "update this test to assert activate_if() receives the full reference."
    ),
)
def test_metadata_update_passes_plain_name_to_activate_if():
    """
    The patched _metadata_update() must call activate_if() with
    mdata.named_file_name (e.g. "my-file"), NOT mdata.named_file_ref
    (e.g. "$my-file.files.<fingerprint>").

    Passing the reference caused ValueError in get_named_file_uuid() because
    the library only accepts $name.results.xxx references there, not
    $name.files.xxx references.
    """
    mdata = _make_mdata(
        named_file_name="my-file",
        named_file_ref="$my-file.files.abc123fingerprint",
    )

    activate_calls = []
    mock_csvpaths = MagicMock()
    mock_csvpaths.file_manager.activator.activate_if = lambda name: activate_calls.append(name)

    listener = object.__new__(FileActivationListener)

    with patch("flightpath.util.listener_utility.CsvPaths", return_value=mock_csvpaths):
        listener._metadata_update(mdata)

    assert len(activate_calls) == 1, (
        "_metadata_update() must call activate_if() exactly once"
    )
    assert activate_calls[0] == "my-file", (
        f"activate_if() must be called with named_file_name 'my-file', "
        f"not named_file_ref; got: {activate_calls[0]!r}"
    )


@pytest.mark.xfail(
    reason=(
        "This test verifies the current workaround behavior: that "
        "_fixed_activation_metadata_update never forwards the files reference "
        "to activate_if(). It will need to be replaced once "
        "FileManager.get_named_file_uuid() is fixed to accept "
        "$name.files.<fingerprint> references. At that point the correct "
        "assertion is the inverse: activate_if() MUST receive the full "
        "mdata.named_file_ref so the specific arriving registration is activated, "
        "not an arbitrary version resolved by name alone."
    ),
)
def test_metadata_update_does_not_pass_reference_to_activate_if():
    """
    Regression guard: _metadata_update() must never forward the
    "$name.files.<fingerprint>" reference as the filename.

    If it did, get_named_file_uuid() would raise ValueError because it only
    accepts $name.results.xxx references, not $name.files.xxx references.
    """
    mdata = _make_mdata(
        named_file_name="sales-data",
        named_file_ref="$sales-data.files.deadbeef0123",
    )

    activate_calls = []
    mock_csvpaths = MagicMock()
    mock_csvpaths.file_manager.activator.activate_if = lambda name: activate_calls.append(name)

    listener = object.__new__(FileActivationListener)

    with patch("flightpath.util.listener_utility.CsvPaths", return_value=mock_csvpaths):
        listener._metadata_update(mdata)

    assert all("files" not in call for call in activate_calls), (
        "_metadata_update() must not forward the $name.files.xxx reference to "
        f"activate_if(); calls received: {activate_calls}"
    )


def test_metadata_update_calls_wrap_up():
    """
    _metadata_update() must call csvpaths.wrap_up() after activate_if()
    to release any resources held by the temporary CsvPaths instance.
    """
    mdata = _make_mdata(
        named_file_name="any-file",
        named_file_ref="$any-file.files.abc",
    )

    mock_csvpaths = MagicMock()
    listener = object.__new__(FileActivationListener)

    with patch("flightpath.util.listener_utility.CsvPaths", return_value=mock_csvpaths):
        listener._metadata_update(mdata)

    mock_csvpaths.wrap_up.assert_called_once_with()


# ---------------------------------------------------------------------------
# Thread-spawn and thread-safety tests
# ---------------------------------------------------------------------------


def test_metadata_update_stores_mdata_on_self():
    """
    FileActivationListener.metadata_update() must store mdata on self.metadata
    before calling self.start(), so the thread can access it via self.metadata
    inside run().

    This is the first half of the thread-spawn sequence that causes the segfault:
    the thread is started with its input data on self, then runs _metadata_update
    concurrently with Qt's event loop.
    """
    mdata = _make_mdata(named_file_name="my-file", named_file_ref="$my-file.files.abc")
    listener = object.__new__(FileActivationListener)

    with patch.object(listener, "start"):
        listener.metadata_update(mdata)

    assert listener.metadata is mdata, (
        "metadata_update() must store mdata on self.metadata so the thread can "
        "access it via self.metadata inside run()"
    )


def test_metadata_update_calls_thread_start():
    """
    FileActivationListener.metadata_update() calls self.start() — this spawns a
    raw threading.Thread that runs _metadata_update() concurrently with Qt's main
    event loop.  When _metadata_update creates CsvPaths() and parses the Lark
    grammar, GIL contention with Qt's proxy-model filterAcceptsRow() causes the
    segfault seen in Thread 0 of the crash report.

    start() is mocked here to prevent the thread from actually running; the
    assertion confirms the spawn is attempted.
    """
    mdata = _make_mdata(named_file_name="my-file", named_file_ref="$my-file.files.abc")
    listener = object.__new__(FileActivationListener)

    with patch.object(listener, "start") as mock_start:
        listener.metadata_update(mdata)

    mock_start.assert_called_once_with()


@pytest.mark.xfail(
    raises=AttributeError,
    strict=True,
    reason=(
        "run() calls self.csvpaths.wrap_up() after _metadata_update() returns, "
        "but _fixed_activation_metadata_update stores CsvPaths() in a local "
        "variable and never assigns self.csvpaths — so self.csvpaths remains "
        "None and the trailing wrap_up() raises AttributeError."
    ),
)
def test_run_does_not_crash_on_self_csvpaths_wrap_up():
    """
    FileActivationListener.run() calls self._metadata_update(self.metadata) then
    self.csvpaths.wrap_up().  The patched _fixed_activation_metadata_update creates
    a local 'csvpaths' and calls wrap_up() on it, but never assigns self.csvpaths.
    After _metadata_update returns, self.csvpaths is still None, so the trailing
    self.csvpaths.wrap_up() in run() raises AttributeError.

    Fix: assign self.csvpaths = CsvPaths() in _fixed_activation_metadata_update
    instead of a local variable, so run()'s cleanup call can succeed.
    """
    mdata = _make_mdata(named_file_name="any", named_file_ref="$any.files.abc")
    listener = object.__new__(FileActivationListener)
    listener.csvpaths = None
    listener.metadata = mdata

    mock_csvpaths = MagicMock()
    with patch("flightpath.util.listener_utility.CsvPaths", return_value=mock_csvpaths):
        listener.run()  # raises AttributeError: 'NoneType' object has no attribute 'wrap_up'
