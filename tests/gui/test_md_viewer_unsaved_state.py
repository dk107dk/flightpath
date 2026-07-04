"""
Tests documenting the MdViewer unsaved-state bug introduced by on_toggle().

Bug report: When a .md file is toggled to raw text view (ctrl/cmd-t), editing
and then closing does not prompt the user to save.

Confirmed root cause: on_toggle() calls _make_editor(), which constructs a new
RawTextEdit.  RawTextEdit.__init__ unconditionally sets self.my_parent.saved = True,
overwriting whatever the flag was before the toggle.  on_toggle() captures `saved`
before calling _make_editor() and calls reset_saved() if it was True — but there
is no path to restore saved=False when the file had unsaved changes before the
toggle.

Specifically broken:
  - Edit in markdown view, toggle to raw text, close: unsaved state silently lost.

NOT broken (confirmed by tests):
  - Edit directly in raw text view (without a prior markdown edit): desaved() chain
    works correctly, saved=False is set, close prompts.

Run with:
    QT_QPA_PLATFORM=offscreen poetry run python -m pytest tests/gui/test_md_viewer_unsaved_state.py -v
"""

import os

from PySide6.QtCore import Qt

from flightpath.util.tabs_utility import TabsUtility as taut
from flightpath.widgets.panels.md_viewer import MdViewer

TIMEOUT = 5000  # ms


def _examples(main, *parts) -> str:
    return os.path.join(main.state.cwd, "examples", *parts)


def _open_md(qtbot, main) -> MdViewer:
    """Open the example README.md and return its MdViewer."""
    path = _examples(main, "first steps", "README.md")
    assert os.path.exists(path), f"Example README.md not found: {path}"
    main.read_validate_and_display_file_for_path(path)
    qtbot.waitUntil(
        lambda: taut.find_tab(main.content.tab_widget, path) is not None,
        timeout=TIMEOUT,
    )
    viewer = taut.find_tab(main.content.tab_widget, path)[1]
    assert isinstance(viewer, MdViewer)
    return viewer


# ---------------------------------------------------------------------------
# Control: editing in markdown (rich) view marks the file unsaved — must pass
# ---------------------------------------------------------------------------


def test_md_markdown_view_edit_marks_unsaved(qtbot, main):
    """
    Editing in the default markdown view must set viewer.saved=False so that
    close_tab() issues a save prompt.  This is the working baseline.
    """
    viewer = _open_md(qtbot, main)
    assert viewer.saved is True
    assert viewer.displaying is True  # default: markdown/rich view

    qtbot.keyClick(viewer.text_edit, Qt.Key_A)

    assert viewer.saved is False, "Markdown-view edit must mark the file unsaved"
    assert not main.content.all_files_are_saved()


# ---------------------------------------------------------------------------
# Confirmed working: editing directly in raw text view does mark unsaved
# (the desaved() delegation chain in RawTextEdit works correctly)
# ---------------------------------------------------------------------------


def test_md_raw_text_view_edit_marks_unsaved(qtbot, main):
    """
    Toggling to raw text view and editing (with no prior markdown edit) must
    set viewer.saved=False.  RawTextEdit.desaved() correctly delegates to
    MdViewer.desaved(), so this path works and close_tab does prompt.
    This test is here to document that the raw-text desaved() chain is not
    the source of the bug.
    """
    viewer = _open_md(qtbot, main)
    assert viewer.saved is True

    # Switch to raw text view
    viewer.on_toggle()
    assert viewer.displaying is False
    qtbot.wait(100)  # let deleteLater() from the old MdTextEdit settle

    qtbot.keyClick(viewer.text_edit, Qt.Key_A)

    assert viewer.saved is False, (
        "Raw-text-view edit must mark the file unsaved via the desaved() chain"
    )
    assert not main.content.all_files_are_saved()


# ---------------------------------------------------------------------------
# Bug: unsaved state made in markdown view is lost when toggling to raw text
# (the actual root cause of the reported symptom)
# ---------------------------------------------------------------------------


def test_md_unsaved_state_survives_toggle_to_raw(qtbot, main):
    """
    Edits made in markdown view must still be reflected as unsaved after
    toggling to raw text.  Fixed in on_toggle() by restoring self.saved
    after _make_editor() resets it.
    """
    viewer = _open_md(qtbot, main)
    assert viewer.saved is True

    # Edit in markdown view — pre-condition
    qtbot.keyClick(viewer.text_edit, Qt.Key_A)
    assert viewer.saved is False, "Pre-condition: markdown edit must mark unsaved"

    # Toggle to raw text — the unsaved state must survive
    viewer.on_toggle()
    qtbot.wait(100)

    assert viewer.saved is False, (
        "viewer.saved must remain False after toggling to raw text; "
        "_make_editor() reset it to True (bug)"
    )
    assert not main.content.all_files_are_saved()
