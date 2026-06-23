"""
pytest-qt tests for OffsetsForm.

Checklist coverage:
  CONFIG > offsets section — offset values saved and applied

== OffsetsForm overview ==

OffsetsForm manages three integer offset fields (days, months, years) that
shift the date returned by DateUtility.now().  The offsets live on class-level
attributes of DateUtility — they are NOT persisted to config.ini.

  on_set()   — reads fields, writes to daut.OFFSET_DAYS / MONTHS / YEARS,
                refreshes the read-only 'now' QLabel with the shifted date
  on_reset() — zeros all three class attributes

The 'now' QLabel shows str(daut.now()), which is a UTC datetime such as:
  "2026-06-28 12:48:42.245798+00:00"

Tests check the YYYY-MM-DD prefix only so microsecond differences between
when the label is set and when the assertion runs do not cause false failures.

== State isolation ==

daut.OFFSET_DAYS / MONTHS / YEARS are class-level attributes that persist
across tests in the same process.  Each test that writes them resets them
inline at the end.  A module-level autouse fixture provides a safety net that
zeros the offsets before each test regardless of what a prior test left behind.

Run with:
  QT_QPA_PLATFORM=offscreen poetry run python -m pytest tests/gui/test_offsets_form.py -v
"""

import datetime

import pytest

from csvpath.util.date_util import DateUtility as daut

# isolated_home and main fixtures provided by conftest.py


# ---------------------------------------------------------------------------
# State isolation
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def zero_date_offsets():
    """Zero DateUtility class offsets before and after every test in this module."""
    daut.OFFSET_DAYS = 0
    daut.OFFSET_MONTHS = 0
    daut.OFFSET_YEARS = 0
    yield
    daut.OFFSET_DAYS = 0
    daut.OFFSET_MONTHS = 0
    daut.OFFSET_YEARS = 0


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _form(main):
    main.open_config()
    form = main.config.config_panel.get_form("offsets")
    assert form is not None, "OffsetsForm must be present in config panel"
    return form


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_offsets_form_now_label_shows_todays_date(qtbot, main):
    """
    With all offsets at zero, the 'now' QLabel must show today's UTC date.

    The label is set to str(daut.now()) in on_set() and on form construction.
    The test calls on_set() with all fields at '0' to guarantee the label is
    freshly set from a known zero-offset state, then checks the YYYY-MM-DD
    prefix against daut.now().date().
    """
    form = _form(main)
    form.days.setText("0")
    form.months.setText("0")
    form.years.setText("0")
    form.on_set()

    expected_date = str(daut.now().date())
    assert form.now.text()[:10] == expected_date, (
        f"now label must show today's date {expected_date!r}; "
        f"got {form.now.text()!r}"
    )


def test_offsets_form_days_offset_advances_date(qtbot, main):
    """
    Setting days=5 and clicking 'Set date offsets' must advance the date shown
    in the 'now' label by exactly 5 days.

    The expected date is computed from daut.now() (still at zero offset) before
    on_set() is called; 5 days are added.  After on_set() the label must contain
    that date's YYYY-MM-DD string.
    """
    form = _form(main)

    base_date = daut.now().date()
    expected_date = str(base_date + datetime.timedelta(days=5))

    form.days.setText("5")
    form.months.setText("0")
    form.years.setText("0")
    form.on_set()

    assert form.now.text()[:10] == expected_date, (
        f"now label must show {expected_date!r} after days=5; "
        f"got {form.now.text()!r}"
    )


def test_offsets_form_months_offset_advances_date(qtbot, main):
    """
    Setting months=1 must advance the displayed date by one calendar month.

    The expected date is computed by adding one month via relativedelta so
    day-of-month clamping (e.g., January 31 → February 28) is handled correctly.
    """
    try:
        from dateutil.relativedelta import relativedelta as rd
    except ImportError:
        pytest.skip("dateutil not available — cannot compute expected month-offset date")

    form = _form(main)

    base = daut.now()
    expected_date = str((base + rd(months=1)).date())

    form.days.setText("0")
    form.months.setText("1")
    form.years.setText("0")
    form.on_set()

    assert form.now.text()[:10] == expected_date, (
        f"now label must show {expected_date!r} after months=1; "
        f"got {form.now.text()!r}"
    )


def test_offsets_form_years_offset_advances_date(qtbot, main):
    """
    Setting years=1 must advance the year shown in the 'now' label by one.

    Checking the year component is sufficient since year-boundary arithmetic
    is simpler than month arithmetic.
    """
    form = _form(main)

    base_year = daut.now().year
    expected_year = str(base_year + 1)

    form.days.setText("0")
    form.months.setText("0")
    form.years.setText("1")
    form.on_set()

    assert form.now.text()[:4] == expected_year, (
        f"now label year must be {expected_year!r} after years=1; "
        f"got {form.now.text()!r}"
    )


def test_offsets_form_on_set_writes_daut_class_attributes(qtbot, main):
    """
    on_set() must write the entered integer values to the DateUtility class
    attributes OFFSET_DAYS, OFFSET_MONTHS, and OFFSET_YEARS.

    These are the authoritative values used by CsvPath Framework for date
    arithmetic — the form is the only GUI entry point to change them.
    """
    form = _form(main)
    form.days.setText("3")
    form.months.setText("2")
    form.years.setText("1")
    form.on_set()

    assert daut.OFFSET_DAYS == 3, (
        f"OFFSET_DAYS must be 3 after on_set(); got {daut.OFFSET_DAYS!r}"
    )
    assert daut.OFFSET_MONTHS == 2, (
        f"OFFSET_MONTHS must be 2 after on_set(); got {daut.OFFSET_MONTHS!r}"
    )
    assert daut.OFFSET_YEARS == 1, (
        f"OFFSET_YEARS must be 1 after on_set(); got {daut.OFFSET_YEARS!r}"
    )


def test_offsets_form_negative_offset_moves_date_back(qtbot, main):
    """
    Negative offset values must be accepted and must shift the date backward.

    days=-3 must result in OFFSET_DAYS==-3 and a now label 3 days in the past.
    """
    form = _form(main)

    base_date = daut.now().date()
    expected_date = str(base_date - datetime.timedelta(days=3))

    form.days.setText("-3")
    form.months.setText("0")
    form.years.setText("0")
    form.on_set()

    assert daut.OFFSET_DAYS == -3, (
        f"OFFSET_DAYS must be -3; got {daut.OFFSET_DAYS!r}"
    )
    assert form.now.text()[:10] == expected_date, (
        f"now label must show {expected_date!r} after days=-3; "
        f"got {form.now.text()!r}"
    )


def test_offsets_form_invalid_input_clears_field(qtbot, main):
    """
    Non-integer input in days/months/years must be cleared after on_set().

    on_set() wraps int() conversion in try/except and calls setText("") on the
    field when conversion fails.  The invalid field is cleared; the other fields
    and the offset class attributes remain at their default (0).
    """
    form = _form(main)
    form.days.setText("not-a-number")
    form.months.setText("0")
    form.years.setText("0")
    form.on_set()

    assert form.days.text() == "", (
        f"days field must be cleared after non-integer input; "
        f"got {form.days.text()!r}"
    )
    assert daut.OFFSET_DAYS == 0, (
        f"OFFSET_DAYS must remain 0 when input is invalid; got {daut.OFFSET_DAYS!r}"
    )


def test_offsets_form_on_reset_zeros_class_attributes(qtbot, main):
    """
    on_reset() must set OFFSET_DAYS, OFFSET_MONTHS, and OFFSET_YEARS back to 0.

    This is the user-facing 'undo all offsets' action.  The test first applies
    non-zero offsets via on_set() then calls on_reset() and verifies the class
    attributes are zeroed.  The 'now' label is not explicitly refreshed by
    on_reset() — only the class attributes are cleared.
    """
    form = _form(main)
    form.days.setText("10")
    form.months.setText("3")
    form.years.setText("2")
    form.on_set()

    assert daut.OFFSET_DAYS == 10, "Precondition: offsets must be set before reset"

    form.on_reset()

    assert daut.OFFSET_DAYS == 0, (
        f"OFFSET_DAYS must be 0 after on_reset(); got {daut.OFFSET_DAYS!r}"
    )
    assert daut.OFFSET_MONTHS == 0, (
        f"OFFSET_MONTHS must be 0 after on_reset(); got {daut.OFFSET_MONTHS!r}"
    )
    assert daut.OFFSET_YEARS == 0, (
        f"OFFSET_YEARS must be 0 after on_reset(); got {daut.OFFSET_YEARS!r}"
    )
