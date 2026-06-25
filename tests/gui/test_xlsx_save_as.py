"""
pytest-qt tests for XLSX file handling and save-as behavior.

Checklist coverage:
  HOME > open XLSX > single default worksheet opens in DataViewer
  HOME > open XLSX with multiple worksheets > worksheet selector / named tab
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

# CPIForecast.xlsx contains two worksheets:
#   'October 2024 CPI Forecast' — 37 rows × 14 cols (the main data)
#   'Test sheet 1'              —  4 rows ×  3 cols (small helper sheet)
SHEET_CPI = "October 2024 CPI Forecast"
SHEET_SMALL = "Test sheet 1"


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


def _open_sheet_and_wait(qtbot, main, sheet_name: str):
    """Open a named worksheet and block until its DataViewer tab appears.

    The tab objectName is 'path#SheetName' — the same key emitted by
    GeneralDataWorker when sheet is not None.
    """
    tab_key = f"{XLSX_PATH}#{sheet_name}"
    main.read_validate_and_display_file_for_path(tab_key)
    qtbot.waitUntil(
        lambda: taut.find_tab(main.content.tab_widget, tab_key) is not None,
        timeout=TIMEOUT,
    )
    return taut.find_tab(main.content.tab_widget, tab_key)[1]


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

#chked
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

#chked
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

#chked
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


# ---------------------------------------------------------------------------
# Tests — XLSX multi-worksheet: open individual sheets
# ---------------------------------------------------------------------------

#chked
def test_xlsx_worksheets_for_path_returns_sheet_names(main):
    """
    _worksheets_for_path() must return all worksheet names for an XLSX file.
    CPIForecast.xlsx has exactly two sheets; both must appear in the result.
    """
    names = main.sidebar._worksheets_for_path(XLSX_PATH)
    assert SHEET_CPI in names, f"Expected '{SHEET_CPI}' in worksheet list: {names}"
    assert SHEET_SMALL in names, f"Expected '{SHEET_SMALL}' in worksheet list: {names}"
    assert len(names) == 2, f"Expected exactly 2 worksheets, got: {names}"

#chked
def test_xlsx_named_worksheet_opens_in_data_viewer(qtbot, main):
    """
    Opening a named worksheet via 'path#SheetName' must produce a DataViewer
    tab whose objectName is 'path#SheetName'.  This is the same path taken
    when the user selects a sheet from the right-click Worksheets sub-menu.
    """
    viewer = _open_sheet_and_wait(qtbot, main, SHEET_SMALL)
    assert isinstance(viewer, DataViewer), (
        f"Worksheet '{SHEET_SMALL}' must open in a DataViewer"
    )

#svk
def test_xlsx_worksheet_has_correct_row_count(qtbot, main):
    """
    The small test sheet has 4 rows of data.  After opening it, the DataViewer
    model must expose exactly those 4 rows (GeneralDataWorker defaults to
    reading the first 66k rows, well above the 4-row ceiling here).
    """
    viewer = _open_sheet_and_wait(qtbot, main, SHEET_SMALL)
    model = viewer.table_view.model()
    assert model is not None, "DataViewer model must be populated after opening worksheet"
    assert model.rowCount() == 4, (
        f"'{SHEET_SMALL}' has 4 rows; model reported {model.rowCount()}"
    )


#chked
def test_xlsx_two_worksheets_open_as_separate_tabs(qtbot, main):
    """
    Opening both worksheets must create two independent DataViewer tabs, each
    keyed by its own 'path#SheetName' objectName.  The tabs must coexist
    without the second opening replacing the first.
    """
    _open_sheet_and_wait(qtbot, main, SHEET_SMALL)
    _open_sheet_and_wait(qtbot, main, SHEET_CPI)

    key_small = f"{XLSX_PATH}#{SHEET_SMALL}"
    key_cpi = f"{XLSX_PATH}#{SHEET_CPI}"

    assert taut.find_tab(main.content.tab_widget, key_small) is not None, (
        f"Tab for '{SHEET_SMALL}' must still exist after opening second sheet"
    )
    assert taut.find_tab(main.content.tab_widget, key_cpi) is not None, (
        f"Tab for '{SHEET_CPI}' must exist"
    )


def test_xlsx_worksheet_save_as_csv(monkeypatch, qtbot, main):
    """
    Saving a worksheet-derived DataViewer via on_save_as() must produce a
    comma-separated CSV containing the worksheet's data.

    Worksheet paths have the form 'file.xlsx#SheetName', so Path.suffix is
    '.xlsx#SheetName' rather than '.xlsx' — on_save() does not detect them
    as XLSX files.  on_save_as() is the correct entry point (triggered by
    right-click Save As or Shift+Ctrl+S).
    """
    viewer = _open_sheet_and_wait(qtbot, main, SHEET_SMALL)
    output = os.path.join(main.state.cwd, "sheet_small.csv")
    parent_ref = []

    monkeypatch.setattr(
        "flightpath.widgets.panels.data_viewer.SaveCsvToDialog",
        _fake_dialog_cls(parent_ref, output, "Comma", ["csv"]),
    )

    viewer.on_save_as()

    assert os.path.isfile(output), f"Expected CSV from worksheet save-as at: {output}"
    with open(output) as f:
        lines = [ln for ln in f.readlines() if ln.strip()]
    assert len(lines) == 4, (
        f"CSV from '{SHEET_SMALL}' must have 4 data rows, got {len(lines)}"
    )

    qtbot.wait(3000)

