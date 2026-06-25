# Unit Test Improvement Plan

Work through these steps in order. Each step is one session.
After all steps are complete, begin the second plan: testability improvements and surface-area coverage.

---

## Step 1 — `test_file_util.py` ✓
- [x] Replace shared `tests/test_resources/deconflict/` with `tmp_path` (isolation fix)
- [x] Convert from `unittest.TestCase` to bare pytest functions
- [x] Add: `None` input to `join_local_overlapped` → `ValueError`
- [x] Add: cloud URL in pathtwo → `ValueError` (empty string does not raise; omitted)
- [x] Add: no-overlap case (pathtwo shares no suffix with pathone) → simple append
- [x] Add: `deconflicted_path` with no existing conflict → returns original name unchanged
- [x] Add: `deconflict_file_name` with many sequential conflicts (0, 1, 2 …)
- [x] Add: `deconflict_file_name` with a file that has no extension
- [x] Add: `split_filename` tests (used internally; 4 cases)

## Step 2 — `test_string_util.py` ✓
- [x] Convert from `unittest.TestCase` to bare pytest functions
- [x] Split into one function per assertion
- [x] Add: `jsonl_text_to_list` with empty string → `[]`
- [x] Add: `jsonl_text_to_list` with a single JSON object → 1-item list
- [x] Add: `jsonl_text_to_list` with malformed JSON → raw string entry returned
- [x] Add: `jsonl_text_to_list` with whitespace-only input → `[]`
- [x] Add: `jsonl_text_to_list` with `None` → `""` (documents current contract)
- [x] Add: `good_name` with empty string → False
- [x] Add: `good_name` with `None` → False
- [x] Add: `good_name` boundary chars for all three ranges + default extras
- [x] Add: `good_name` colon quirk (range(48,59) includes ':') pinned
- [x] Add: `sanitize_json` — 4 tests (control chars, printable, space boundary, empty)

## Step 3 — `test_api_versions.py` ✓
- [x] Convert from `unittest.TestCase` to bare pytest functions
- [x] Split into one function per assertion
- [x] Fix 2 pre-existing broken tests: source raises ValueError/ModuleNotFoundError, not ApiException
- [x] Add: `_parse_versions` with `None` → ValueError
- [x] Add: `_parse_versions` with empty list → ValueError
- [x] Add: `_parse_versions` with non-`v`-prefixed string → ValueError
- [x] Add: `_parse_versions` with bare integer, float, and arbitrary word
- [x] Add: `_parse_versions` with mixed valid/invalid list → raises on first bad entry
- [x] Add: `connect` with `v2` → FlightPathServerApiV2
- [x] Add: `connect` with `["v1", "v2"]` → prefers highest (v2)
- [x] Add: `connect` falls back to lower version when highest is unimplemented
- [x] Add: `connect` with malformed version string propagates ValueError

## Step 4 — `test_test_data_utility.py` ✓
- [x] Convert from `unittest.TestCase` to bare pytest functions
- [x] Add: no `test-data` annotation → None
- [x] Add: no comment block at all → None
- [x] Add: empty string → None
- [x] Add: multiple csvpaths (MARKER-separated) → first annotation returned
- [x] Add: annotation only in second block → found and returned
- [x] Add: whitespace around path value → stripped
- [x] Add: malformed annotation (colon, empty value) → None
- [x] Add: None input → AttributeError (documents missing None guard)

## Step 5 — `test_templates.py` ✓
- [x] Convert from `unittest.TestCase` to bare pytest functions
- [x] Split 19 assertion groups into 27 named test functions
- [x] Fix: entire old test suite was testing dead code — refactor replaced old logic
  with temu.validate(); invalid inputs now raise ValueError, not return ("", True)
- [x] Add: end=None → ValueError; end without colon → ValueError
- [x] Add: t=None → ("", True) — only non-raising rejection path
- [x] Add: 7 valid template forms (run_dir and filename modes)
- [x] Add: 10 invalid forms — wrong/missing end marker, leading slash, starts with
  end marker, double end marker, illegal chars, non-numeric colon tokens
- [x] Note: rstrip('/:filename') strips chars individually so short paths like
  "a/:filename" collapse to "" and fail; tests use longer safe paths

## Step 6 — `test_insert_metadata.py` ✓
- [x] Convert from `unittest.TestCase` to bare pytest functions
- [x] Split 4 assertion groups into 4 named test functions
- [x] Add: position == len(text) → ValueError("out of string")
- [x] Add: position well past end → ValueError
- [x] Add: empty addto → comment text left intact (2 variants)
- [x] Add: None addto → literal "None" inserted (documents missing guard)
- [x] Add: no ~ markers in text → synthetic comment created

## Step 7 — `test_env_file.py` → `test_config_form.py` ✓
- [x] Create test_config_form.py; stub out test_env_file.py (not deleted)
- [x] Bare pytest functions throughout
- [x] Split 11 path permutations into 11 named tests
- [x] Add: path=None with cwd=None → "env" (short-circuits before cwd guard)
- [x] Add: real path with cwd=None → ValueError
- [x] Add: current_project=None → falls back to basename(cwd)
- [x] Add: "env" sentinel with surrounding spaces → "env"
- [x] Add: cwd not ending with current_project → cwd used as root regardless
- [x] Add: absolute path from a different project → only basename kept

## Step 8 — `test_inspector.py` ✓
- [x] Remove test.html write (was debug-only; no tmp_path needed)
- [x] Convert from `unittest.TestCase` to bare pytest functions
- [x] Add 6 Inspector.info tests: dict type, filename, required keys,
  header names matching CSV, header_count consistency, total_lines > 0
- [x] Add 6 HtmlGenerator tests: non-empty string, filename in output,
  all 3 column headers in output, keyword sections present, path=None→None,
  output > 1 KB
- [x] Add _compile_scan: c=0 → "*" (clamped to 0 is falsy → wildcard)
- [x] Add _compile_scan: c == sample_size → "0-50" (strict > so no clamp)
- [x] Add _compile_scan: c < sample_size → clamped (already tested; added c=1)
- [x] Add _compile_scan: from_line=5 → "5-15" range

## Step 9 — `test_examples.py` ✓
- [x] Convert from `unittest.TestCase` to bare pytest functions
- [x] Replace shared tests/test_resources/examples/ with tmp_path
- [x] Assert both filenames (test.csv, test.csvpath) explicitly
- [x] Assert both copied files have non-empty content
- [x] Assert copied CSV is byte-for-byte identical to source
- [x] Assert source directory is unchanged after copy
- [x] Sanity check: tmp_path empty before / populated after

## Step 10 — New `test_tabs_utility.py` ✓
- [x] Create `tests/gui/test_tabs_utility.py` with `_require_qapp` autouse fixture
- [x] `find_tab`: found (first/middle/last), not found, empty, widget identity check
- [x] `tab_index`: found, first, not found raises, empty raises
- [x] `tab_index_if`: found, not found → -1, empty → -1
- [x] `tab_index_by_name`: found (first/last), not found raises, empty raises
- [x] `tab_index_by_name_if`: found, not found → -1, empty → -1
- [x] `tabs`: count, order preserved, empty → [], single widget
- [x] `has_type`: match → True, no match → False, empty → False
- [x] `select_tab` by int: sets index, index=0, out-of-range raises
- [x] `select_tab` by widget: found sets index, not found → False
- [x] `select_tab_widget`: found sets index, not found → False, empty → False
- [x] Bug pinned: select_tab raises ValueError with literal "{i}" (broken f-string)

## Step 11 — Survey and fill utility class gaps ✓

Surveyed all 30 files in flightpath/util/.  Deferred to plan 2: KeyUtility
(Qt key events), StyleUtility (private helpers + Qt widgets), LogUtility
(needs real Config), FileCollector (Qt dialog), RunInfo/GeneratorUtility/
ServerUtility (external deps).  Skipped: DataConst (constants).

### New: `test_json_utility.py` (10 tests)
- [x] `is_jsonl`: .jsonl, .jsonlines, .ndjson all match
- [x] Non-matching: .json, .csv, empty string, uppercase .JSONL → False
- [x] Quirk pinned: no-dot "ndjson" suffix also matches (bare string check in source)
- [x] None → AttributeError (missing guard documented)

### New: `test_os_utility.py` (15 tests)
- [x] `is_sandboxed`: env var set → True, absent → False, empty string → True
- [x] `is_windows/is_mac/is_unix`: all three platforms via monkeypatch
- [x] `file_system_open_cmd`: "open"/"explorer"/"xdg-open" per platform

### Extended: `test_file_util.py` (+17 tests)
- [x] `is_a`: match, multi-ext list, no match, None guard, case sensitive, last ext wins, empty list
- [x] `count_files`: empty dir, two files, grows after add
- [x] `is_new_writable`: True for new path, cleans up probe, False if exists, False if parent missing
- [x] `is_writable_dir`: True for writable dir, False for missing dir
- [x] `move_file_to_numbered`: moves file, preserves content, no-op if source missing

### Extended: `test_string_util.py` (+4 tests)
- [x] `jsonl_text_to_lines`: returns str (not list, despite annotation), no newline for 1 object, joined for 2, empty → ""
- [x] Bug noted: return type annotation says `list[str]` but method returns `str`
