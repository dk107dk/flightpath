"""
Unit tests for Inspector and HtmlGenerator
(flightpath/inspect/inspector.py, flightpath/util/html_generator.py).

Inspector.info runs a CsvPath against the test file and returns a dict of
statistics (header names, line counts, type distributions, etc.).
HtmlGenerator.load_and_transform renders those stats into HTML via Jinja2.
Inspector._compile_scan builds the CsvPath scan range string from sample_size
and from_line settings.

The original test wrote test.html to the project root — that write is removed.

Run with:
  QT_QPA_PLATFORM=offscreen poetry run python -m pytest tests/test_inspector.py -v
"""

import os
from pathlib import Path

import pytest

from flightpath.inspect.inspector import Inspector
from flightpath.util.file_utility import FileUtility as fiut
from flightpath.util.html_generator import HtmlGenerator

# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

_TESTS = Path(__file__).parent.parent
CSV_PATH    = str(_TESTS / "test_resources" / "examples" / "test.csv")
TEMPLATE_PATH = fiut.make_app_path(
    f"assets{os.sep}help{os.sep}templates{os.sep}file_details.html"
)

# Headers known to be in test.csv — used to verify HTML content
KNOWN_HEADERS = ["firstname", "lastname", "say"]


def _inspector(sample_size=25, from_line=1):
    insp = Inspector(main=None, filepath=CSV_PATH)
    insp.sample_size = sample_size
    insp.from_line   = from_line
    return insp


# ---------------------------------------------------------------------------
# Inspector.info — data dictionary
# ---------------------------------------------------------------------------


def test_info_returns_dict():
    insp = _inspector()
    assert isinstance(insp.info, dict)


def test_info_contains_filename():
    """info['name'] must be the basename of the CSV, not the full path."""
    assert _inspector().info["name"] == "test.csv"


def test_info_contains_all_expected_keys():
    expected = {
        "name", "file", "sample_size", "from_line", "scan",
        "header_count", "headers", "total_lines", "data_lines",
        "blank_lines", "lines_with_blanks", "duplicate_lines",
        "header_details",
    }
    assert expected.issubset(_inspector().info.keys())


def test_info_headers_match_csv_columns():
    assert _inspector().info["headers"] == KNOWN_HEADERS


def test_info_header_count_matches_headers():
    info = _inspector().info
    assert info["header_count"] == len(info["headers"])


def test_info_total_lines_is_positive():
    assert _inspector().info["total_lines"] > 0


# ---------------------------------------------------------------------------
# HtmlGenerator.load_and_transform — HTML output
# ---------------------------------------------------------------------------


def test_html_is_non_empty_string():
    insp = _inspector()
    html = HtmlGenerator.load_and_transform(TEMPLATE_PATH, insp.info)
    assert isinstance(html, str) and len(html.strip()) > 0


def test_html_contains_filename():
    insp = _inspector()
    html = HtmlGenerator.load_and_transform(TEMPLATE_PATH, insp.info)
    assert "test.csv" in html


def test_html_contains_all_column_headers():
    insp = _inspector()
    html = HtmlGenerator.load_and_transform(TEMPLATE_PATH, insp.info)
    for header in KNOWN_HEADERS:
        assert header in html, f"Expected header {header!r} not found in HTML"


def test_html_contains_statistics_sections():
    """The template renders total, header, and duplicate sections."""
    insp = _inspector()
    html = HtmlGenerator.load_and_transform(TEMPLATE_PATH, insp.info).lower()
    for keyword in ("total", "header", "duplicate"):
        assert keyword in html, f"Expected keyword {keyword!r} not in HTML"


def test_html_path_none_returns_none():
    """load_and_transform returns None silently when path is None."""
    result = HtmlGenerator.load_and_transform(None, {})
    assert result is None


def test_html_output_is_substantial():
    """The rendered file detail page should have meaningful content (>1 KB)."""
    insp = _inspector()
    html = HtmlGenerator.load_and_transform(TEMPLATE_PATH, insp.info)
    assert len(html) > 1000


# ---------------------------------------------------------------------------
# Inspector._compile_scan — scan range string
# ---------------------------------------------------------------------------


def test_compile_scan_c_larger_than_sample_size():
    """c >> sample_size: sample_size is not clamped; result is 0-{sample_size}."""
    insp = Inspector(main=None, filepath=CSV_PATH)
    insp.sample_size = 50
    assert insp._compile_scan(c=5000) == "0-50"


def test_compile_scan_c_smaller_than_sample_size():
    """c < sample_size: sample_size is clamped to c."""
    insp = Inspector(main=None, filepath=CSV_PATH)
    insp.sample_size = 50
    assert insp._compile_scan(c=5) == "0-5"


def test_compile_scan_c_equal_to_sample_size():
    """c == sample_size: the > check is strict so no clamp occurs; result is 0-{sample_size}."""
    insp = Inspector(main=None, filepath=CSV_PATH)
    insp.sample_size = 50
    assert insp._compile_scan(c=50) == "0-50"


def test_compile_scan_c_zero_returns_wildcard():
    """
    c=0 clamps sample_size to 0, which is falsy.  The else branch activates
    and returns '*' (scan all lines) rather than '0-0'.  This is the behaviour
    when the visible grid has no rows.
    """
    insp = Inspector(main=None, filepath=CSV_PATH)
    insp.sample_size = 50
    assert insp._compile_scan(c=0) == "*"


def test_compile_scan_with_from_line_produces_range():
    """When from_line > 1, the scan is from_line to from_line+sample_size."""
    insp = Inspector(main=None, filepath=CSV_PATH)
    insp.sample_size = 10
    insp.from_line   = 5
    assert insp._compile_scan(c=100) == "5-15"


def test_compile_scan_single_row_visible():
    """c=1 clamps sample_size to 1; result is '0-1'."""
    insp = Inspector(main=None, filepath=CSV_PATH)
    insp.sample_size = 50
    assert insp._compile_scan(c=1) == "0-1"


# ---------------------------------------------------------------------------
# Inspector.compile_match — no disk side-effects
# ---------------------------------------------------------------------------


def test_compile_match_returns_nonempty_string():
    """compile_match must return a non-empty string containing csvpath expressions."""
    insp = _inspector()
    result = insp.compile_match()
    assert isinstance(result, str) and len(result.strip()) > 0


def test_compile_match_does_not_write_file(tmp_path, monkeypatch):
    """compile_match must not write __inspector.csvpath (removed debug artifact)."""
    monkeypatch.chdir(tmp_path)
    insp = _inspector()
    insp.compile_match()
    assert not (tmp_path / "__inspector.csvpath").exists(), (
        "__inspector.csvpath must not be written to disk by compile_match"
    )
