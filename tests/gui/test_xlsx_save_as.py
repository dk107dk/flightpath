"""
pytest-qt tests for XLSX file handling and save-as behavior.

Checklist coverage:
  HOME > save, save-as > grid (XLSX — forced save-as to CSV)
  HOME > delimiters > save data as new delimiter (from XLSX source)

XLSX files cannot be saved back as XLSX; DataViewer.on_save() detects the
.xlsx/.xls extension and unconditionally redirects to on_save_as(), which
shows SaveCsvToDialog.  The dialog is monkeypatched in redirect and write
tests so SaveCsvToDialog._save() executes without a visible dialog.

Test resource: tests/test_resources/CPIForecast.xlsx
  Row 0: title row  ("Changes in Consumer Price Indexes, 2022 through 2025", ...)
  Row 1: column headers  ("Consumer Price Index item", ...)
  Row 2: sub-headers  ("", "Percent", ...)

Run with:
  QT_QPA_PLATFORM=offscreen poetry run python -m pytest tests/gui/test_xlsx_save_as.py -v
"""

import os

from PySide6.QtCore import Qt

from flightpath.util.tabs_utility import TabsUtility as taut
from flightpath.widgets.panels.data_viewer import DataViewer

# isolated_home and main fixtures are provided by conftest.py

TIMEOUT = 8000  # ms — GeneralDataWorker runs on the Qt thread pool

XLSX_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "test_resources",
    "CPIForecast.xlsx",
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _open_and_wait(qtbot, main):
    """Open CPIForecast.xlsx and block until its DataViewer tab appears."""
    main.read_validate_and_display_file_for_path(XLSX_PATH)
    qtbot.waitUntil(
        lambda: taut.find_tab(main.content.tab_widget, XLSX_PATH) is not None,
        timeout=TIMEOUT,
    )
    return taut.find_tab(main.content.tab_widget, XLSX_PATH)[1]


def _fake_dialog_cls(parent_ref: list, output_path: str, delimiter: str, exts: list):
    """
    Return a SaveCsvToDialog replacement that immediately saves to output_path
    when show() is called.  parent_ref is a one-element list used to capture
    the DataViewer passed as parent= so the test can verify it.
    """
    class _FakeSaveCsvToDialog:
        def __init__(self, *, parent, main, path):
            parent_ref.append(parent)

        def show(self):
            parent_ref[0]._save_one_of(
                path=output_path,
                delimiter=delimiter,
                quotechar="Double quotes",
                exts=exts,
            )

    return _FakeSaveCsvToDialog


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_xlsx_opens_in_data_viewer(qtbot, main):
    """
    Opening CPIForecast.xlsx must produce a DataViewer tab with a populated
    model.  Row 0 must contain the spreadsheet's title string so we know the
    file was actually parsed, not just opened as binary.
    """
    viewer = _open_and_wait(qtbot, main)
    assert isinstance(viewer, DataViewer), "XLSX must open in a DataViewer"

    model = viewer.table_view.model()
    assert model is not None, "DataViewer model must be set after opening XLSX"
    assert model.rowCount() > 0, "DataViewer model must have rows"

    title_cell = model.data(model.index(0, 0), Qt.DisplayRole)
    assert title_cell and "Consumer Price Index" in str(title_cell), (
        "First cell must contain the CPI spreadsheet title"
    )


def test_xlsx_save_redirects_to_save_as(monkeypatch, qtbot, main):
    """
    Calling on_save() on an XLSX DataViewer must redirect to on_save_as(),
    which shows SaveCsvToDialog.  XLSX cannot be saved back to XLSX; the
    redirect is unconditional regardless of path.
    """
    viewer = _open_and_wait(qtbot, main)
    dialog_shown = []

    class _FakeSaveCsvToDialog:
        def __init__(self, *, parent, main, path):
            dialog_shown.append(path)

        def show(self):
            pass  # do not write — we only verify the redirect happened

    monkeypatch.setattr(
        "flightpath.widgets.panels.data_viewer.SaveCsvToDialog",
        _FakeSaveCsvToDialog,
    )

    viewer.on_save()

    assert len(dialog_shown) == 1, (
        "on_save() on an XLSX file must redirect to SaveCsvToDialog exactly once"
    )


def test_xlsx_save_as_comma_csv(monkeypatch, qtbot, main):
    """
    Saving an XLSX file via the (monkeypatched) SaveCsvToDialog with Comma
    delimiter must write a valid comma-separated CSV.  The header row must
    contain commas; the file must be non-empty.
    """
    viewer = _open_and_wait(qtbot, main)
    output = os.path.join(main.state.cwd, "cpi_comma.csv")
    parent_ref = []

    monkeypatch.setattr(
        "flightpath.widgets.panels.data_viewer.SaveCsvToDialog",
        _fake_dialog_cls(parent_ref, output, "Comma", ["csv"]),
    )

    viewer.on_save()

    assert os.path.isfile(output), f"Expected CSV output at: {output}"
    with open(output) as f:
        first_line = f.readline()
    assert "," in first_line, "Comma-delimited XLSX export must contain commas in header"


def test_xlsx_save_as_pipe_delimited(monkeypatch, qtbot, main):
    """
    Saving an XLSX file via the (monkeypatched) SaveCsvToDialog with Pipe
    delimiter must write a pipe-separated file.  This is the main delimiter
    variant test for XLSX: same SaveCsvToDialog flow as JSONL but from a
    real spreadsheet source.
    """
    viewer = _open_and_wait(qtbot, main)
    output = os.path.join(main.state.cwd, "cpi_pipe.psv")
    parent_ref = []

    monkeypatch.setattr(
        "flightpath.widgets.panels.data_viewer.SaveCsvToDialog",
        _fake_dialog_cls(parent_ref, output, "Pipe", ["csv", "psv"]),
    )

    viewer.on_save()

    assert os.path.isfile(output), f"Expected pipe-delimited output at: {output}"
    with open(output) as f:
        first_line = f.readline()
    assert "|" in first_line, "Pipe-delimited XLSX export must contain | in header"
