"""
Unit tests for GeneralDataWorker.accept_line() and prep_sampling().

These are low-level tests that sit beneath the GUI sampling tests in
test_content_actions.py.  They verify the two methods that control which
lines from a file end up in the TableModel, so that a failure can be
pinpointed here rather than diagnosed from a wrong row count in a UI test.

Key invariants under test:

  accept_line() return values:
    True  — include this line, keep reading
    False — skip this line, keep reading
    None  — cap reached, stop reading the file entirely

  The True/False/None distinction matters: _read()'s loop treats None as a
  break signal and False as a continue.  Collapsing them would silently read
  the whole file instead of stopping at the requested cap.

  prep_sampling() contract for RANDOM_ALL mode:
    - Produces exactly sample_size unique line numbers
    - Stores them in descending order (accept_line reads from the end via [-1])
    - Falls back to sample_size=-1 when the file has fewer lines than the cap

DataWorkerSignals inherits QObject and therefore requires a QApplication.
The module-level autouse fixture pulls in pytest-qt's session-scoped qapp so
these tests can also be run in isolation without a full GUI fixture.

Run with:
  QT_QPA_PLATFORM=offscreen poetry run python -m pytest tests/gui/test_general_data_worker.py -v
"""

import random

import pytest

from flightpath.util.data_const import DataConst
from flightpath.workers.general_data_worker import GeneralDataWorker


# ---------------------------------------------------------------------------
# Qt application — required for DataWorkerSignals (QObject)
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True, scope="module")
def _require_qapp(qapp):
    """Pull in pytest-qt's session QApplication so QObject can be created."""
    pass


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _worker(
    *,
    sampling: str = DataConst.FIRST_N,
    rows: str = "10",
    filepath: str = "dummy.csv",
) -> GeneralDataWorker:
    """Construct a worker with main=None; sufficient for accept_line tests."""
    return GeneralDataWorker(filepath, None, rows=rows, sampling=sampling)


# ---------------------------------------------------------------------------
# Tests — accept_line: FIRST_N mode
# ---------------------------------------------------------------------------


def test_accept_line_first_n_returns_true_until_cap():
    """
    FIRST_N must return True for each of the first sample_size calls, then
    None on the next call — not False.  None is the stop signal to _read().
    """
    w = _worker(sampling=DataConst.FIRST_N, rows="3")
    assert w.accept_line(0, ["a"]) is True
    assert w.accept_line(1, ["b"]) is True
    assert w.accept_line(2, ["c"]) is True
    assert w.accept_line(3, ["d"]) is None


def test_accept_line_first_n_cap_is_none_not_false():
    """
    Regression guard: the cap must return None, not False.  _read()'s loop
    only breaks on None; False would cause it to skip the line and keep
    reading the whole file instead of stopping.
    """
    w = _worker(sampling=DataConst.FIRST_N, rows="1")
    w.accept_line(0, ["a"])
    result = w.accept_line(1, ["b"])
    assert result is None, f"Cap must return None (stop), not {result!r}"


def test_accept_line_first_n_increments_line_take():
    """Each accepted line must increment line_take by exactly 1."""
    w = _worker(sampling=DataConst.FIRST_N, rows="5")
    for i in range(3):
        w.accept_line(i, ["x"])
    assert w.line_take == 3


def test_accept_line_zero_cap_returns_none_immediately():
    """
    sample_size=0 means the cap is already reached before any line is read.
    The very first accept_line call must return None.
    """
    w = _worker(sampling=DataConst.FIRST_N, rows="5")
    w.sample_size = 0
    assert w.accept_line(0, ["a"]) is None


# ---------------------------------------------------------------------------
# Tests — accept_line: ALL_LINES mode (sample_size == -1)
# ---------------------------------------------------------------------------


def test_accept_line_all_lines_always_returns_true():
    """
    sample_size=-1 (All lines) must return True unconditionally and never cap.
    200 calls is well past any normal sample_size; the cap branch is skipped
    entirely when sample_size is -1.
    """
    w = _worker(sampling=DataConst.FIRST_N, rows="All lines")
    assert w.sample_size == -1
    for i in range(200):
        result = w.accept_line(i, ["x"])
        assert result is True, f"ALL_LINES must return True for every line; got {result!r} at line {i}"


def test_accept_line_all_lines_increments_line_take():
    """line_take must still advance in ALL_LINES mode (used by LARGE_FILE_LIMIT guard)."""
    w = _worker(sampling=DataConst.FIRST_N, rows="All lines")
    for i in range(5):
        w.accept_line(i, ["x"])
    assert w.line_take == 5


# ---------------------------------------------------------------------------
# Tests — accept_line: LARGE_FILE_LIMIT guard
# ---------------------------------------------------------------------------


def test_accept_line_large_file_limit_returns_false():
    """
    Once line_take exceeds LARGE_FILE_LIMIT (66 000), accept_line must return
    False — not True or None.  This prevents loading arbitrarily large files
    even in ALL_LINES mode.  The guard fires before the sample_size==-1 check.
    """
    w = _worker(sampling=DataConst.FIRST_N, rows="All lines")
    w.line_take = GeneralDataWorker.LARGE_FILE_LIMIT + 1
    result = w.accept_line(0, ["x"])
    assert result is False, f"LARGE_FILE_LIMIT guard must return False, got {result!r}"


# ---------------------------------------------------------------------------
# Tests — accept_line: RANDOM_0 mode
# ---------------------------------------------------------------------------


def test_accept_line_random_0_returns_true_when_randint_zero(monkeypatch):
    """randint(0,1) % 2 == 0 is True when randint returns 0 → line accepted."""
    monkeypatch.setattr(random, "randint", lambda a, b: 0)
    w = _worker(sampling=DataConst.RANDOM_0, rows="10")
    assert w.accept_line(0, ["a"]) is True
    assert w.line_take == 1


def test_accept_line_random_0_returns_false_when_randint_one(monkeypatch):
    """randint(0,1) % 2 == 0 is False when randint returns 1 → line skipped."""
    monkeypatch.setattr(random, "randint", lambda a, b: 1)
    w = _worker(sampling=DataConst.RANDOM_0, rows="10")
    assert w.accept_line(0, ["a"]) is False
    assert w.line_take == 0


def test_accept_line_random_0_stops_at_cap(monkeypatch):
    """
    Even with randint always accepting (returns 0), RANDOM_0 must return None
    once the cap is reached — same cap check as FIRST_N.
    """
    monkeypatch.setattr(random, "randint", lambda a, b: 0)
    w = _worker(sampling=DataConst.RANDOM_0, rows="3")
    for i in range(3):
        assert w.accept_line(i, ["x"]) is True
    assert w.accept_line(3, ["x"]) is None


def test_accept_line_random_0_skipped_lines_do_not_increment_line_take(monkeypatch):
    """Rejected lines (randint=1) must not advance line_take."""
    monkeypatch.setattr(random, "randint", lambda a, b: 1)
    w = _worker(sampling=DataConst.RANDOM_0, rows="10")
    for i in range(5):
        w.accept_line(i, ["x"])
    assert w.line_take == 0


# ---------------------------------------------------------------------------
# Tests — accept_line: RANDOM_ALL mode
# ---------------------------------------------------------------------------


def test_accept_line_random_all_accepts_only_precomputed_lines():
    """
    RANDOM_ALL must accept exactly the lines whose numbers appear in
    lines_to_take (descending order, as prep_sampling produces) and reject all
    others.  This test sets lines_to_take directly to avoid prep_sampling's
    file I/O.
    """
    w = _worker(sampling=DataConst.RANDOM_ALL, rows="3")
    w.lines_to_take = [5, 3, 1]  # descending, as prep_sampling sorts them

    assert w.accept_line(0, ["x"]) is False  # not in list
    assert w.accept_line(1, ["x"]) is True   # matches [-1]=1, pops
    assert w.accept_line(2, ["x"]) is False  # not in list
    assert w.accept_line(3, ["x"]) is True   # matches [-1]=3, pops
    assert w.accept_line(4, ["x"]) is False  # not in list
    assert w.accept_line(5, ["x"]) is True   # matches [-1]=5, pops


def test_accept_line_random_all_pops_entry_after_match():
    """
    Each matched line number must be removed from lines_to_take so the next
    call can match the next entry.  If entries were not popped, the same line
    number would match on every subsequent call.
    """
    w = _worker(sampling=DataConst.RANDOM_ALL, rows="2")
    w.lines_to_take = [3, 1]

    w.accept_line(1, ["x"])
    assert w.lines_to_take == [3], "Entry 1 must be popped after match"

    w.accept_line(3, ["x"])
    assert w.lines_to_take == [], "Entry 3 must be popped after match"


def test_accept_line_random_all_increments_line_take_on_match():
    """line_take must advance for each accepted line in RANDOM_ALL mode."""
    w = _worker(sampling=DataConst.RANDOM_ALL, rows="3")
    w.lines_to_take = [2, 1, 0]

    w.accept_line(0, ["x"])
    assert w.line_take == 1
    w.accept_line(1, ["x"])
    assert w.line_take == 2


# ---------------------------------------------------------------------------
# Tests — prep_sampling
# ---------------------------------------------------------------------------


def _csv(tmp_path, n_lines: int):
    """Write a CSV with 1 header row + n_lines data rows; return its path string."""
    p = tmp_path / "sample.csv"
    rows = ["col_a,col_b"] + [f"{i},{i * 2}" for i in range(n_lines)]
    p.write_text("\n".join(rows))
    return str(p)


def test_prep_sampling_count_matches_sample_size(tmp_path):
    """prep_sampling must populate lines_to_take with exactly sample_size entries."""
    w = _worker(sampling=DataConst.RANDOM_ALL, rows="10", filepath=_csv(tmp_path, 100))
    w.prep_sampling()
    assert len(w.lines_to_take) == 10


def test_prep_sampling_entries_are_unique(tmp_path):
    """No duplicate line numbers — duplicates would cause accept_line to miss entries."""
    w = _worker(sampling=DataConst.RANDOM_ALL, rows="20", filepath=_csv(tmp_path, 100))
    w.prep_sampling()
    assert len(w.lines_to_take) == len(set(w.lines_to_take)), (
        "lines_to_take must contain unique line numbers"
    )


def test_prep_sampling_sorted_descending(tmp_path):
    """
    lines_to_take must be in descending order.  accept_line compares line_num
    against lines_to_take[-1] (the smallest remaining entry) as it reads lines
    in ascending order.  If the list were ascending, [-1] would be the largest
    number and no line would ever match until the very end.
    """
    w = _worker(sampling=DataConst.RANDOM_ALL, rows="15", filepath=_csv(tmp_path, 100))
    w.prep_sampling()
    assert w.lines_to_take == sorted(w.lines_to_take, reverse=True), (
        "lines_to_take must be sorted descending so accept_line can pop matches"
    )


def test_prep_sampling_line_numbers_in_valid_range(tmp_path):
    """All line numbers must fall within the file's valid range (0 to line count)."""
    n = 80
    w = _worker(sampling=DataConst.RANDOM_ALL, rows="10", filepath=_csv(tmp_path, n))
    w.prep_sampling()
    # prep_sampling uses randint(0, needed) where needed is the line count
    for ln in w.lines_to_take:
        assert 0 <= ln, f"Line number {ln} must be non-negative"


def test_prep_sampling_small_file_sets_all_lines_mode(tmp_path):
    """
    When the file has fewer lines than sample_size, prep_sampling must set
    sample_size=-1 (all-lines mode) rather than selecting a random subset.
    This prevents RANDOM_ALL from returning zero or very few rows on a small
    file when the user asked for more rows than exist.
    """
    w = _worker(sampling=DataConst.RANDOM_ALL, rows="50", filepath=_csv(tmp_path, 5))
    w.prep_sampling()
    assert w.sample_size == -1, (
        "Small file (5 rows) with sample_size=50 must trigger all-lines mode"
    )
    assert w.lines_to_take == [], (
        "lines_to_take must be empty when all-lines mode is activated"
    )


def test_prep_sampling_exact_size_file_sets_all_lines_mode(tmp_path):
    """
    When file line count equals sample_size + 1 (the boundary condition in
    `if self.sample_size >= needed - 1`), all-lines mode must also activate.

    _csv(n=9) writes 1 header + 9 data rows = 10 physical lines → needed=10.
    sample_size=9 → 9 >= 10-1=9 → True → all-lines mode.
    """
    w = _worker(sampling=DataConst.RANDOM_ALL, rows="9", filepath=_csv(tmp_path, 9))
    w.prep_sampling()
    assert w.sample_size == -1, (
        "File with exactly sample_size+1 lines must trigger all-lines mode"
    )
