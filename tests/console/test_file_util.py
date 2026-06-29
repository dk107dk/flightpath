"""
Unit tests for FileUtility (flightpath/util/file_utility.py).

Covers:
  join_local_overlapped  — overlap-stripping path join for local paths
  deconflict_file_name   — sequential rename when a filename already exists
  deconflicted_path      — convenience wrapper that returns the full path
  split_filename         — basename splitter used internally by deconflict logic
  is_a                   — extension membership check using Path.suffix
  count_files            — count entries in a directory
  is_new_writable        — True if path does not exist and parent is writable
  is_writable_dir        — True if directory exists and is writable
  move_file_to_numbered  — moves a file into a backup dir with a numeric suffix

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
    """If pathone starts with a separator, the result must also start with that separator."""
    pathone = "/a/b/c/d"
    result = fiut.join_local_overlapped(pathone, "d/e/f.ini")
    assert result.startswith(pathone[0])


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


# ---------------------------------------------------------------------------
# is_a — extension check
# ---------------------------------------------------------------------------


def test_is_a_matching_extension_returns_true():
    assert fiut.is_a("report.csv", ["csv"]) is True


def test_is_a_extension_in_list_of_many():
    assert fiut.is_a("report.csv", ["txt", "csv", "tsv"]) is True


def test_is_a_non_matching_extension_returns_false():
    assert fiut.is_a("report.csv", ["txt"]) is False


def test_is_a_none_path_returns_false():
    """is_a has an explicit None guard."""
    assert fiut.is_a(None, ["csv"]) is False


def test_is_a_case_sensitive():
    """Extension comparison is case-sensitive: .CSV does not match 'csv'."""
    assert fiut.is_a("report.CSV", ["csv"]) is False


def test_is_a_uses_last_extension():
    """Path.suffix returns the last extension, so .gz matches but .tar does not."""
    assert fiut.is_a("archive.tar.gz", ["gz"]) is True
    assert fiut.is_a("archive.tar.gz", ["tar"]) is False


def test_is_a_empty_list_returns_false():
    assert fiut.is_a("report.csv", []) is False


# ---------------------------------------------------------------------------
# count_files
# ---------------------------------------------------------------------------


def test_count_files_empty_dir(tmp_path):
    assert fiut.count_files(str(tmp_path)) == 0


def test_count_files_with_two_files(tmp_path):
    (tmp_path / "a.txt").write_text("a")
    (tmp_path / "b.txt").write_text("b")
    assert fiut.count_files(str(tmp_path)) == 2


def test_count_files_grows_after_adding_file(tmp_path):
    before = fiut.count_files(str(tmp_path))
    (tmp_path / "new.txt").write_text("x")
    assert fiut.count_files(str(tmp_path)) == before + 1


# ---------------------------------------------------------------------------
# is_new_writable
# ---------------------------------------------------------------------------


def test_is_new_writable_true_for_new_path(tmp_path):
    """A path that does not exist yet in a writable directory returns True."""
    path = str(tmp_path / "new_file.txt")
    result = fiut.is_new_writable(path)
    assert result is True


def test_is_new_writable_cleans_up_probe_file(tmp_path):
    """is_new_writable must remove the probe file it creates."""
    path = str(tmp_path / "probe.txt")
    fiut.is_new_writable(path)
    assert not os.path.exists(path)


def test_is_new_writable_false_when_file_already_exists(tmp_path):
    """An already-existing path is not writable-as-new."""
    path = tmp_path / "existing.txt"
    path.write_text("data")
    assert fiut.is_new_writable(str(path)) is False


def test_is_new_writable_false_when_parent_dir_missing(tmp_path):
    path = str(tmp_path / "no_such_dir" / "file.txt")
    assert fiut.is_new_writable(path) is False


# ---------------------------------------------------------------------------
# is_writable_dir
# ---------------------------------------------------------------------------


def test_is_writable_dir_true_for_existing_writable_dir(tmp_path):
    assert fiut.is_writable_dir(str(tmp_path)) is True


def test_is_writable_dir_false_for_missing_dir(tmp_path):
    missing = str(tmp_path / "no_such_dir")
    assert fiut.is_writable_dir(missing) is False


# ---------------------------------------------------------------------------
# move_file_to_numbered
# ---------------------------------------------------------------------------


def test_move_file_to_numbered_moves_file_to_backup_dir(tmp_path):
    """The source file is moved; backup dir is created; file is renamed with _N suffix."""
    src = tmp_path / "app.log"
    src.write_text("log content")
    backup_dir = str(tmp_path / "bak")
    fiut.move_file_to_numbered(str(src), backup_dir)
    assert not src.exists()
    files = os.listdir(backup_dir)
    assert len(files) == 1
    assert files[0].startswith("app.log_")


def test_move_file_to_numbered_preserves_content(tmp_path):
    """The moved file must have the same content as the source."""
    src = tmp_path / "data.log"
    src.write_text("important data")
    backup_dir = str(tmp_path / "bak")
    fiut.move_file_to_numbered(str(src), backup_dir)
    backed_up = os.path.join(backup_dir, os.listdir(backup_dir)[0])
    assert open(backed_up).read() == "important data"


def test_move_file_to_numbered_no_op_when_source_missing(tmp_path):
    """If the source does not exist, the method returns silently and creates nothing."""
    missing = str(tmp_path / "ghost.log")
    backup_dir = str(tmp_path / "bak")
    fiut.move_file_to_numbered(missing, backup_dir)
    assert not os.path.exists(backup_dir)
