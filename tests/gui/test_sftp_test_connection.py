"""
Tests for the SFTP "Test Connection" button in SftpForm.

Two groups:
  1. SftpTestWorker unit tests — call worker.run() synchronously with
     paramiko monkeypatched; no thread pool involved.
  2. SftpForm integration tests — instantiate the form, click the button,
     let the worker run in the real thread pool (paramiko still mocked),
     and verify the result message.

Run with:
    QT_QPA_PLATFORM=offscreen poetry run python -m pytest tests/gui/test_sftp_test_connection.py -v
"""

import socket

import paramiko
import pytest
from PySide6.QtCore import QThreadPool
from PySide6.QtWidgets import QWidget

from flightpath.dialogs.sftp.sftp_form import SftpForm
from flightpath.util.message_utility import MessageUtility as meut
from flightpath.workers.sftp_test_worker import SftpTestWorker

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


class _MockParent(QWidget):
    def update_server(self) -> None:
        pass

    def remove_server(self, name: str) -> None:
        pass


class _MockMain:
    pass


def _make_form(qtbot) -> SftpForm:
    parent = _MockParent()
    qtbot.addWidget(parent)
    form = SftpForm(main=_MockMain(), parent=parent)
    qtbot.addWidget(form)
    return form


def _ssh_client_succeeds():
    class _Client:
        def set_missing_host_key_policy(self, policy) -> None:
            pass

        def connect(self, host, **kwargs) -> None:
            pass

        def close(self) -> None:
            pass

    return _Client()


def _ssh_client_raises(exc):
    class _Client:
        def set_missing_host_key_policy(self, policy) -> None:
            pass

        def connect(self, host, **kwargs) -> None:
            raise exc

        def close(self) -> None:
            pass

    return _Client()


# ---------------------------------------------------------------------------
# 1. SftpTestWorker unit tests
# ---------------------------------------------------------------------------


def test_worker_emits_true_on_success(qtbot, monkeypatch):
    """
    A successful paramiko connection must emit finished(True, ...) with a
    message confirming success.
    """
    monkeypatch.setattr(paramiko, "SSHClient", _ssh_client_succeeds)

    results = []
    worker = SftpTestWorker(server="host", port=22, username="u", password="p")
    worker.signals.finished.connect(lambda ok, msg: results.append((ok, msg)))
    worker.run()

    assert len(results) == 1
    assert results[0][0] is True
    assert "successfully" in results[0][1].lower()


def test_worker_emits_false_on_auth_failure(qtbot, monkeypatch):
    """
    AuthenticationException must emit finished(False, ...) mentioning
    authentication.
    """
    monkeypatch.setattr(
        paramiko,
        "SSHClient",
        lambda: _ssh_client_raises(paramiko.AuthenticationException()),
    )

    results = []
    worker = SftpTestWorker(server="host", port=22, username="u", password="bad")
    worker.signals.finished.connect(lambda ok, msg: results.append((ok, msg)))
    worker.run()

    assert results[0][0] is False
    assert "authentication" in results[0][1].lower()


def test_worker_emits_false_on_no_valid_connections(qtbot, monkeypatch):
    """
    NoValidConnectionsError must emit finished(False, ...) mentioning the server.
    """
    exc = paramiko.ssh_exception.NoValidConnectionsError({("host", 22): Exception("refused")})
    monkeypatch.setattr(paramiko, "SSHClient", lambda: _ssh_client_raises(exc))

    results = []
    worker = SftpTestWorker(server="host", port=22, username="u", password="p")
    worker.signals.finished.connect(lambda ok, msg: results.append((ok, msg)))
    worker.run()

    assert results[0][0] is False
    assert "server" in results[0][1].lower()


def test_worker_emits_false_on_timeout(qtbot, monkeypatch):
    """
    socket.timeout must emit finished(False, ...) mentioning timeout.
    """
    monkeypatch.setattr(
        paramiko, "SSHClient", lambda: _ssh_client_raises(socket.timeout())
    )

    results = []
    worker = SftpTestWorker(server="host", port=22, username="u", password="p")
    worker.signals.finished.connect(lambda ok, msg: results.append((ok, msg)))
    worker.run()

    assert results[0][0] is False
    assert "timed out" in results[0][1].lower()


def test_worker_emits_false_on_gaierror(qtbot, monkeypatch):
    """
    socket.gaierror must emit finished(False, ...) mentioning host not found.
    """
    monkeypatch.setattr(
        paramiko,
        "SSHClient",
        lambda: _ssh_client_raises(socket.gaierror("Name or service not known")),
    )

    results = []
    worker = SftpTestWorker(server="host", port=22, username="u", password="p")
    worker.signals.finished.connect(lambda ok, msg: results.append((ok, msg)))
    worker.run()

    assert results[0][0] is False
    assert "host not found" in results[0][1].lower()


def test_worker_emits_false_on_generic_exception(qtbot, monkeypatch):
    """
    An unexpected exception must emit finished(False, ...) containing the
    exception message so the user has something actionable.
    """
    monkeypatch.setattr(
        paramiko,
        "SSHClient",
        lambda: _ssh_client_raises(Exception("unexpected internal error")),
    )

    results = []
    worker = SftpTestWorker(server="host", port=22, username="u", password="p")
    worker.signals.finished.connect(lambda ok, msg: results.append((ok, msg)))
    worker.run()

    assert results[0][0] is False
    assert "unexpected internal error" in results[0][1]


def test_worker_raises_on_empty_server(qtbot):
    """
    Constructing SftpTestWorker with an empty server must raise ValueError
    immediately rather than failing silently at connect time.
    """
    with pytest.raises(ValueError):
        SftpTestWorker(server="", port=22, username="u", password="p")


# ---------------------------------------------------------------------------
# 2. SftpForm integration tests
# ---------------------------------------------------------------------------


def test_test_connection_button_exists(qtbot):
    """SftpForm must expose a 'Test Connection' button."""
    form = _make_form(qtbot)
    assert hasattr(form, "test_button"), "SftpForm must have a test_button attribute"
    assert form.test_button.text() == "Test Connection"


def test_test_connection_shows_missing_server_message(qtbot, monkeypatch):
    """
    Clicking Test Connection with an empty server field must show a warning
    via meut.message2 and must NOT submit a worker to the thread pool.
    """
    captured = []
    monkeypatch.setattr(meut, "message2", lambda **kw: captured.append(kw))

    form = _make_form(qtbot)
    form.server.setText("")
    form.test_connection()

    assert len(captured) == 1
    assert "server" in captured[0]["title"].lower() or "server" in captured[0]["msg"].lower()
    assert form.test_button.isEnabled(), "Button must stay enabled when server is missing"


def test_test_connection_disables_button_during_test(qtbot, monkeypatch):
    """
    test_connection() must disable the test button and change its text to
    'Testing…' before submitting the worker, then restore them on completion.
    """
    monkeypatch.setattr(paramiko, "SSHClient", _ssh_client_succeeds)
    monkeypatch.setattr(meut, "message2", lambda **kw: None)

    form = _make_form(qtbot)
    form.server.setText("sftp.example.com")
    form.port.setText("22")
    form.username.setText("user")
    form.password.setText("pass")

    form.test_connection()

    # Button must be disabled immediately after test_connection() returns
    # (before the thread finishes)
    assert not form.test_button.isEnabled()
    assert form.test_button.text() == "Testing…"

    # Wait for the thread pool to finish, then for the slot to run
    QThreadPool.globalInstance().waitForDone(5000)
    qtbot.waitUntil(lambda: form.test_button.isEnabled(), timeout=5000)

    assert form.test_button.text() == "Test Connection"


def test_test_connection_success_shows_message(qtbot, monkeypatch):
    """
    A successful connection must call meut.message2 with a success title
    and re-enable the button.
    """
    monkeypatch.setattr(paramiko, "SSHClient", _ssh_client_succeeds)

    captured = []
    monkeypatch.setattr(meut, "message2", lambda **kw: captured.append(kw))

    form = _make_form(qtbot)
    form.server.setText("sftp.example.com")
    form.port.setText("22")
    form.username.setText("user")
    form.password.setText("pass")

    form.test_connection()

    QThreadPool.globalInstance().waitForDone(5000)
    qtbot.waitUntil(lambda: len(captured) > 0, timeout=5000)

    assert captured[0]["title"] == "Connection Successful"
    assert form.test_button.isEnabled()


def test_test_connection_failure_shows_message(qtbot, monkeypatch):
    """
    An authentication failure must call meut.message2 with a failure title
    and re-enable the button.
    """
    monkeypatch.setattr(
        paramiko,
        "SSHClient",
        lambda: _ssh_client_raises(paramiko.AuthenticationException()),
    )

    captured = []
    monkeypatch.setattr(meut, "message2", lambda **kw: captured.append(kw))

    form = _make_form(qtbot)
    form.server.setText("sftp.example.com")
    form.port.setText("22")
    form.username.setText("user")
    form.password.setText("wrong")

    form.test_connection()

    QThreadPool.globalInstance().waitForDone(5000)
    qtbot.waitUntil(lambda: len(captured) > 0, timeout=5000)

    assert captured[0]["title"] == "Connection Failed"
    assert "authentication" in captured[0]["msg"].lower()
    assert form.test_button.isEnabled()


def test_test_connection_defaults_port_to_22(qtbot, monkeypatch):
    """
    If the port field is empty, test_connection() must default to port 22.
    """
    connected_ports = []

    class _CapturingClient:
        def set_missing_host_key_policy(self, policy) -> None:
            pass

        def connect(self, host, port=22, **kwargs) -> None:
            connected_ports.append(port)

        def close(self) -> None:
            pass

    monkeypatch.setattr(paramiko, "SSHClient", _CapturingClient)
    monkeypatch.setattr(meut, "message2", lambda **kw: None)

    form = _make_form(qtbot)
    form.server.setText("sftp.example.com")
    form.port.setText("")
    form.username.setText("u")
    form.password.setText("p")

    form.test_connection()

    QThreadPool.globalInstance().waitForDone(5000)
    qtbot.waitUntil(lambda: len(connected_ports) > 0, timeout=5000)

    assert connected_ports[0] == 22


# ---------------------------------------------------------------------------
# 3. SftpTab integration tests (Integrations config panel)
# ---------------------------------------------------------------------------


def _sftp_tab(main):
    """Return the live SftpTab from a fully initialised MainWindow."""
    main.open_config()
    form = main.config.config_panel.get_form("listeners")
    assert form is not None, "ListenersForm must be present in config panel"
    tab = form.tab_groups.get("sftp")
    assert tab is not None, "sftp tab must exist in ListenersForm tab_groups"
    return tab


def test_sftp_tab_test_button_exists(qtbot, main):
    """SftpTab must expose a 'Test Connection' button."""
    tab = _sftp_tab(main)
    assert hasattr(tab, "test_button"), "SftpTab must have a test_button attribute"
    assert tab.test_button.text() == "Test Connection"


def test_sftp_tab_shows_missing_server_message(qtbot, main, monkeypatch):
    """
    Calling test_connection() with an empty server field must show a warning
    via meut.message2 and must NOT submit a worker to the thread pool.
    """
    captured = []
    monkeypatch.setattr(meut, "message2", lambda **kw: captured.append(kw))

    tab = _sftp_tab(main)
    tab.server.setText("")
    tab.test_connection()

    assert len(captured) == 1
    assert (
        "server" in captured[0]["title"].lower()
        or "server" in captured[0]["msg"].lower()
    )
    assert tab.test_button.isEnabled(), "Button must stay enabled when server is missing"


def test_sftp_tab_success_shows_message(qtbot, main, monkeypatch):
    """
    A successful connection probe must call meut.message2 with a success
    title and leave the button enabled.
    """
    monkeypatch.setattr(paramiko, "SSHClient", _ssh_client_succeeds)

    captured = []
    monkeypatch.setattr(meut, "message2", lambda **kw: captured.append(kw))

    tab = _sftp_tab(main)
    tab.server.setText("sftp.example.com")
    tab.port.setText("22")
    tab.username.setText("user")
    tab.password.setText("pass")

    tab.test_connection()

    QThreadPool.globalInstance().waitForDone(5000)
    qtbot.waitUntil(lambda: len(captured) > 0, timeout=5000)

    assert captured[0]["title"] == "Connection Successful"
    assert tab.test_button.isEnabled()


def test_sftp_tab_failure_shows_message(qtbot, main, monkeypatch):
    """
    An authentication failure must call meut.message2 with a failure title
    and leave the button enabled.
    """
    monkeypatch.setattr(
        paramiko,
        "SSHClient",
        lambda: _ssh_client_raises(paramiko.AuthenticationException()),
    )

    captured = []
    monkeypatch.setattr(meut, "message2", lambda **kw: captured.append(kw))

    tab = _sftp_tab(main)
    tab.server.setText("sftp.example.com")
    tab.port.setText("22")
    tab.username.setText("user")
    tab.password.setText("wrong")

    tab.test_connection()

    QThreadPool.globalInstance().waitForDone(5000)
    qtbot.waitUntil(lambda: len(captured) > 0, timeout=5000)

    assert captured[0]["title"] == "Connection Failed"
    assert "authentication" in captured[0]["msg"].lower()
    assert tab.test_button.isEnabled()
