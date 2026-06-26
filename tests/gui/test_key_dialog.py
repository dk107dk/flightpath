"""
pytest-qt tests for NewKeyDialog and the "Create new API key" flow in ServerForm.

Checklist coverage:
  SERVER PANEL > create new key — key displayed in dialog

== NewKeyDialog overview ==

NewKeyDialog is opened from ServerForm._create_key() when the user clicks the
"Create new API key" button.  The dialog:
  - Shows three required fields: key_name, key_owner, key_owner_contact
  - On "Create key" click (do_key_create):
      1. Validates all three fields are non-empty; shows a warning if any is blank
      2. Calls parent.api.create_key(key_name=..., owner=..., owner_contact=...)
      3. On success: clears the form rows and displays the new key string in a
         QScrollArea (key_area); changes "Cancel" to "Close"; hides "Create key"
      4. On failure: calls failed_callback(msg=..., code=...) and rejects the dialog
  - __init__ calls self.exec() immediately after building the layout

== Why exec() is patched ==

NewKeyDialog.__init__ ends with self.exec(), which blocks the Qt event loop.
Patching NewKeyDialog.exec to a no-op lets the constructor complete without
blocking so tests can interact with the dialog's slots directly.

Run with:
  QT_QPA_PLATFORM=offscreen poetry run python -m pytest tests/gui/test_key_dialog.py -v
"""

from unittest.mock import MagicMock, patch

import pytest

from flightpath.util.api.server_api import Result
from flightpath.util.message_utility import MessageUtility
from flightpath.dialogs.new_key_dialog import NewKeyDialog

# isolated_home and main fixtures provided by conftest.py


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_api():
    """MagicMock API with ping and create_key pre-configured."""
    api = MagicMock()
    api.ping.return_value = Result(True, {"message": "ok"}, None, 200)
    api.create_key.return_value = Result(
        True, {"api_key": "fpk-test-abc123"}, None, 201
    )
    return api


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _open_server_form(main):
    main.open_config()
    form = main.config.config_panel.get_form("server")
    assert form is not None, "ServerForm must be present in config panel"
    return form


def _wire_mock(form, mock_api, *, host="http://localhost:19999", key="test-api-key"):
    form._api = mock_api
    form.host.setText(host)
    form.key.setText(key)


def _make_key_dialog(main, mock_api, monkeypatch):
    """Create a NewKeyDialog without blocking on exec().

    NewKeyDialog.__init__ calls self.exec() as its last statement.  Patching
    it to a no-op lets the constructor run to completion so tests can interact
    with the dialog's widgets and call do_key_create() directly.
    """
    form = _open_server_form(main)
    _wire_mock(form, mock_api)

    monkeypatch.setattr(NewKeyDialog, "exec", lambda self: None)

    dialog = NewKeyDialog(parent=form, failed_callback=form._create_key_failed)
    return dialog, form


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_new_key_dialog_calls_api_with_correct_fields(monkeypatch, qtbot, main, mock_api):
    """
    Filling in all three required fields and calling do_key_create() must call
    api.create_key() with the exact key_name, owner, and owner_contact values.

    do_key_create() strips whitespace and passes each field as a keyword argument.
    """
    dialog, form = _make_key_dialog(main, mock_api, monkeypatch)
    qtbot.addWidget(dialog)

    dialog.key_name.setText("ci-key")
    dialog.key_owner.setText("Test Owner")
    dialog.key_owner_contact.setText("test@example.com")

    dialog.do_key_create()

    mock_api.create_key.assert_called_once()
    kwargs = mock_api.create_key.call_args.kwargs
    assert kwargs.get("key_name") == "ci-key", (
        f"create_key must receive key_name='ci-key'; got {kwargs.get('key_name')!r}"
    )
    assert kwargs.get("owner") == "Test Owner", (
        f"create_key must receive owner='Test Owner'; got {kwargs.get('owner')!r}"
    )
    assert kwargs.get("owner_contact") == "test@example.com", (
        f"create_key must receive owner_contact='test@example.com'; "
        f"got {kwargs.get('owner_contact')!r}"
    )


def test_new_key_dialog_success_displays_key(monkeypatch, qtbot, main, mock_api):
    """
    After a successful create_key() call, do_key_create() must:
      - populate key_area with the returned API key string
      - hide the "Create key" button
      - relabel "Cancel" as "Close"

    The key is displayed in a QScrollArea (key_area) whose widget is a QLabel
    containing the new key.  This is the only moment the user can see and copy
    the key — the dialog makes that explicit with a warning label.
    """
    dialog, _ = _make_key_dialog(main, mock_api, monkeypatch)
    qtbot.addWidget(dialog)

    dialog.key_name.setText("my-key")
    dialog.key_owner.setText("Alice")
    dialog.key_owner_contact.setText("alice@example.com")

    dialog.do_key_create()

    assert dialog.key_area is not None, (
        "key_area must be set after a successful key creation"
    )
    key_label = dialog.key_area.widget()
    assert key_label is not None, "key_area must contain a widget (QLabel)"
    assert key_label.text() == "fpk-test-abc123", (
        f"key_area label must show the returned API key; got {key_label.text()!r}"
    )
    assert not dialog.create_button.isVisible(), (
        "Create key button must be hidden after key is displayed"
    )
    assert dialog.cancel_button.text() == "Close", (
        f"Cancel button must read 'Close' after key is displayed; "
        f"got {dialog.cancel_button.text()!r}"
    )


def test_new_key_dialog_validation_requires_all_fields(monkeypatch, qtbot, main, mock_api):
    """
    do_key_create() must show a warning and not call api.create_key() when any
    required field (key_name, key_owner, or key_owner_contact) is empty.

    The guard checks all three stripped values; if any is '' or None, it shows
    a MessageUtility.warning2 and returns immediately.
    """
    dialog, _ = _make_key_dialog(main, mock_api, monkeypatch)
    qtbot.addWidget(dialog)

    warnings = []
    monkeypatch.setattr(
        MessageUtility,
        "warning2",
        lambda **kw: warnings.append(kw.get("msg", "")),
    )

    # Leave key_owner empty — only fill key_name and contact
    dialog.key_name.setText("my-key")
    dialog.key_owner.setText("")
    dialog.key_owner_contact.setText("owner@example.com")

    dialog.do_key_create()

    assert len(warnings) == 1, (
        f"Exactly one warning must be shown for missing required field; "
        f"got {len(warnings)}"
    )
    mock_api.create_key.assert_not_called()


def test_new_key_dialog_failure_invokes_failed_callback(monkeypatch, qtbot, main, mock_api):
    """
    When api.create_key() returns a failure Result, do_key_create() must invoke
    failed_callback with the error message and status code.

    ServerForm._create_key_failed is the real callback: it shows a warning2
    dialog with the code and message.  The test monkeypatches warning2 so no
    dialog is shown, and captures the message to verify it contains the
    expected status code.
    """
    mock_api.create_key.return_value = Result(False, None, "Forbidden", 403)

    dialog, _ = _make_key_dialog(main, mock_api, monkeypatch)
    qtbot.addWidget(dialog)

    warnings = []
    monkeypatch.setattr(
        MessageUtility,
        "warning2",
        lambda **kw: warnings.append(kw.get("msg", "")),
    )

    dialog.key_name.setText("bad-key")
    dialog.key_owner.setText("Bob")
    dialog.key_owner_contact.setText("bob@example.com")

    dialog.do_key_create()

    assert len(warnings) == 1, (
        f"Exactly one warning must be shown on API failure; got {len(warnings)}"
    )
    assert "403" in warnings[0] or "Cannot create" in warnings[0], (
        f"Warning must reference the failure; got {warnings[0]!r}"
    )
    assert dialog.key_area is None, (
        "key_area must remain None when key creation fails"
    )


def test_do_key_create_bootstraps_keyless_api_when_no_key_on_form(
    monkeypatch, qtbot, main, mock_api
):
    """
    do_key_create() must fall back to a keyless FlightPathServerApi when
    parent.api raises ValueError (no API key entered on the server form).

    This is the first-key bootstrap scenario: a brand-new server has no
    existing keys, so the user cannot fill in the API-key field before
    clicking "Create new API key".  The server allows unauthenticated
    create_key calls when no keys exist.

    Bug: do_key_create() called self.my_parent.api unconditionally.  The api
    property raises ValueError when the key field is empty, propagating as an
    uncaught exception rather than attempting the call without authentication.

    Fix: do_key_create() catches ValueError from self.my_parent.api and falls
    back to FlightPathServerApi(self.my_parent.hostname) — a keyless connection
    that omits the access_token header entirely.
    """
    form = _open_server_form(main)
    form._api = None
    form.host.setText("http://localhost:19999")
    form.key.setText("")

    monkeypatch.setattr(NewKeyDialog, "exec", lambda self: None)

    dialog = NewKeyDialog(parent=form, failed_callback=form._create_key_failed)
    qtbot.addWidget(dialog)

    dialog.key_name.setText("bootstrap-key")
    dialog.key_owner.setText("Bootstrap Owner")
    dialog.key_owner_contact.setText("boot@example.com")

    with patch(
        "flightpath.dialogs.new_key_dialog.FlightPathServerApi",
        return_value=mock_api,
    ):
        dialog.do_key_create()

    mock_api.create_key.assert_called_once_with(
        key_name="bootstrap-key",
        owner="Bootstrap Owner",
        owner_contact="boot@example.com",
    )


def test_do_key_create_shows_warning_when_server_unreachable_on_bootstrap(
    monkeypatch, qtbot, main
):
    """
    When the server is unreachable and parent.api raises ValueError, the
    fallback FlightPathServerApi() call raises ApiException.  do_key_create()
    must show a warning dialog rather than propagating the exception.
    """
    from flightpath.util.api.server_api import ApiException

    form = _open_server_form(main)
    form._api = None
    form.host.setText("http://localhost:19999")
    form.key.setText("")

    monkeypatch.setattr(NewKeyDialog, "exec", lambda self: None)

    dialog = NewKeyDialog(parent=form, failed_callback=form._create_key_failed)
    qtbot.addWidget(dialog)

    dialog.key_name.setText("key-name")
    dialog.key_owner.setText("Owner")
    dialog.key_owner_contact.setText("owner@example.com")

    warnings = []
    monkeypatch.setattr(
        MessageUtility,
        "warning2",
        lambda **kw: warnings.append(kw.get("msg", "")),
    )

    with patch(
        "flightpath.dialogs.new_key_dialog.FlightPathServerApi",
        side_effect=ApiException("connection refused"),
    ):
        dialog.do_key_create()

    assert len(warnings) == 1, (
        f"A warning must be shown when the server is unreachable; got {len(warnings)}"
    )
    assert "connection refused" in warnings[0].lower() or "connect" in warnings[0].lower(), (
        f"Warning must mention the connection error; got {warnings[0]!r}"
    )
