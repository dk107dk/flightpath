"""
Unit tests for FileUtility (flightpath/util/file_utility.py).

Covers:
  join_local_overlapped — overlap-stripping path join for local paths
  deconflict_file_name  — sequential rename when a filename already exists
  deconflicted_path     — convenience wrapper that returns the full path
  split_filename        — basename splitter used internally by deconflict logic

Run with:
  poetry run python -m pytest tests/test_file_util.py -v
"""

import os

import pytest

from flightpath.util.file_utility import FileUtility as fiut


# ---------------------------------------------------------------------------
# join_local_overlapped
# ---------------------------------------------------------------------------


def test_join_local_overlapped_removes_shared_tail():
    """When the last part of pathone matches the first part of pathtwo, it is
    removed to avoid duplication: /a/b/c/d + d/e/f.ini → /a/b/c/d/e/f.ini."""
    assert fiut.join_local_overlapped("/a/b/c/d", "d/e/f.ini") == "/a/b/c/d/e/f.ini"


def test_join_local_overlapped_no_overlap_with_filename():
    """When pathtwo is a single filename with no match, paths are simply joined."""
    assert fiut.join_local_overlapped("/a/b/c/d", "f.ini") == "/a/b/c/d/f.ini"


def test_join_local_overlapped_no_overlap_with_subpath():
    """When pathtwo's first part does not match pathone's last part, simple join."""
    assert fiut.join_local_overlapped("/fish/blue", "rodents/red.ini") == (
        "/fish/blue/rodents/red.ini"
    )


def test_join_local_overlapped_preserves_leading_sep():
    """If pathone starts with os.sep, the result must also start with os.sep."""
    result = fiut.join_local_overlapped("/a/b/c/d", "d/e/f.ini")
    assert result.startswith(os.sep)


def test_join_local_overlapped_pathone_none_raises():
    with pytest.raises(ValueError, match="pathone"):
        fiut.join_local_overlapped(None, "d/e/f.ini")


def test_join_local_overlapped_pathtwo_none_raises():
    with pytest.raises(ValueError, match="pathtwo"):
        fiut.join_local_overlapped("/a/b/c", None)


def test_join_local_overlapped_cloud_url_in_pathone_raises():
    """Cloud/remote URLs in pathone must be rejected."""
    with pytest.raises(ValueError):
        fiut.join_local_overlapped("s3://bucket/key", "key/file.csv")


def test_join_local_overlapped_cloud_url_in_pathtwo_raises():
    """Cloud/remote URLs in pathtwo must also be rejected."""
    with pytest.raises(ValueError):
        fiut.join_local_overlapped("/local/path", "s3://bucket/file.csv")


def test_join_local_overlapped_multi_overlap_removes_one_level():
    """The overlap loop only removes one matching tail segment per iteration.
    /a/b/c/d + d/e → /a/b/c/d/e (one 'd' removed)."""
    result = fiut.join_local_overlapped("/a/b/c/d", "d/e")
    assert result == "/a/b/c/d/e"


# ---------------------------------------------------------------------------
# split_filename — internal utility used by deconflict logic
# ---------------------------------------------------------------------------


def test_split_filename_with_extension():
    assert fiut.split_filename("report.csv") == ["report", "csv"]


def test_split_filename_no_extension():
    """A filename with no dot returns an empty string for the extension part."""
    assert fiut.split_filename("report") == ["report", ""]


def test_split_filename_multiple_dots_splits_on_first():
    """Only the first dot is used as the extension separator."""
    assert fiut.split_filename("archive.tar.gz") == ["archive", "tar.gz"]


def test_split_filename_strips_directory():
    """split_filename operates on the basename only."""
    result = fiut.split_filename("/some/dir/report.csv")
    assert result == ["report", "csv"]


# ---------------------------------------------------------------------------
# deconflict_file_name
# ---------------------------------------------------------------------------


def test_deconflict_file_name_no_conflict_returns_original(tmp_path):
    """When the file does not exist, deconflict_file_name returns the basename
    unchanged — no numbering suffix is added."""
    path = str(tmp_path / "report.csv")
    assert fiut.deconflict_file_name(path) == "report.csv"


def test_deconflict_file_name_one_conflict(tmp_path):
    """When report.csv already exists, the first available name is report(0).csv."""
    p = tmp_path / "report.csv"
    p.write_text("x")
    assert fiut.deconflict_file_name(str(p)) == "report(0).csv"


def test_deconflict_file_name_sequential_conflicts(tmp_path):
    """Sequential conflicts produce report(0).csv, report(1).csv, … in order."""
    base = tmp_path / "report.csv"
    base.write_text("x")

    name0 = fiut.deconflict_file_name(str(base))
    assert name0 == "report(0).csv"
    (tmp_path / name0).write_text("x")

    name1 = fiut.deconflict_file_name(str(base))
    assert name1 == "report(1).csv"
    (tmp_path / name1).write_text("x")

    name2 = fiut.deconflict_file_name(str(base))
    assert name2 == "report(2).csv"


def test_deconflict_file_name_no_extension_no_conflict(tmp_path):
    """A file with no extension and no conflict returns the name unchanged."""
    path = str(tmp_path / "README")
    assert fiut.deconflict_file_name(path) == "README"


def test_deconflict_file_name_no_extension_with_conflict(tmp_path):
    """A file with no extension gets (N) appended directly to the name."""
    p = tmp_path / "README"
    p.write_text("x")
    assert fiut.deconflict_file_name(str(p)) == "README(0)"


def test_deconflict_file_name_returned_name_does_not_exist(tmp_path):
    """The returned name must point to a path that does not yet exist."""
    p = tmp_path / "data.csv"
    p.write_text("x")
    name = fiut.deconflict_file_name(str(p))
    assert not (tmp_path / name).exists()


# ---------------------------------------------------------------------------
# deconflicted_path
# ---------------------------------------------------------------------------


def test_deconflicted_path_no_conflict_returns_joined(tmp_path):
    """When the filename does not exist, returns path/name unchanged."""
    result = fiut.deconflicted_path(str(tmp_path), "output.csv")
    assert result == str(tmp_path / "output.csv")


def test_deconflicted_path_with_conflict_appends_counter(tmp_path):
    """When output.csv already exists, returns path to output(0).csv."""
    (tmp_path / "output.csv").write_text("x")
    result = fiut.deconflicted_path(str(tmp_path), "output.csv")
    assert result == str(tmp_path / "output(0).csv")


def test_deconflicted_path_result_does_not_exist(tmp_path):
    """The returned path must not point to an existing file."""
    (tmp_path / "output.csv").write_text("x")
    result = fiut.deconflicted_path(str(tmp_path), "output.csv")
    assert not os.path.exists(result)
