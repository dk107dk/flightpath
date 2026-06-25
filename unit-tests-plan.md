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

## Step 5 — `test_templates.py`
- [ ] Convert from `unittest.TestCase` to bare pytest functions
- [ ] Split the 17 assertion groups into 17+ individually named test functions
- [ ] Add: `None` input to `clean_or_reject`
- [ ] Add: empty string for the `end` parameter
- [ ] Add: path that is nothing but slashes
- [ ] Add: very long path (stress boundary)

## Step 6 — `test_insert_metadata.py`
- [ ] Convert from `unittest.TestCase` to bare pytest functions
- [ ] Split 4 assertion groups into 4 named test functions
- [ ] Add: `position` beyond end of text
- [ ] Add: empty string for `addto`

## Step 7 — `test_env_file.py` → `test_config_form.py`
- [ ] Rename file to `test_config_form.py`
- [ ] Convert from `unittest.TestCase` to bare pytest functions
- [ ] Split 10 path permutations into 10 named test functions
- [ ] Add: `None` for `cwd`
- [ ] Add: `cwd` that doesn't end with `current_project`
- [ ] Add: absolute `path` that lives under a different project directory

## Step 8 — `test_inspector.py`
- [ ] Replace `test.html` side-effect with `tmp_path` (or remove file write)
- [ ] Convert from `unittest.TestCase` to bare pytest functions
- [ ] Replace `html is not None and len > 0` with specific content assertions
  (known column names from test.csv, expected section headings)
- [ ] Add: `_compile_scan` with `c=0`
- [ ] Add: `_compile_scan` with `c` equal to `sample_size` exactly
- [ ] Add: `_compile_scan` with `c` less than `sample_size`

## Step 9 — `test_examples.py`
- [ ] Convert from `unittest.TestCase` to bare pytest functions
- [ ] Replace output directory with `tmp_path` (eliminates need for cleanup)
- [ ] Replace `len(listdir()) == 2` with assertions on actual filenames
- [ ] Add: spot-check that at least one copied file has non-empty content

## Step 10 — New `test_tabs_utility.py`
- [ ] Create `tests/gui/test_tabs_utility.py` with `_require_qapp` autouse fixture
- [ ] `find_tab`: tab found returns `(index, widget)`
- [ ] `find_tab`: tab not found returns `None`
- [ ] `find_tab`: empty tab widget returns `None`
- [ ] `select_tab`: by valid index sets `currentIndex`
- [ ] `select_tab`: index out of range raises `ValueError`
- [ ] `select_tab`: by widget delegates to `select_tab_widget`
- [ ] `tab_index`: found returns correct index
- [ ] `tab_index`: not found raises `ValueError`
- [ ] `tab_index_if`: found returns correct index; not found returns `-1`
- [ ] `tab_index_by_name` and `tab_index_by_name_if`: same found/not-found split

## Step 11 — Survey and fill utility class gaps
- [ ] Read full source of `JsonUtility` — list untested methods
- [ ] Read full source of `FileUtility` — list methods beyond what step 1 covers
- [ ] Read full source of `StringUtility` — list methods beyond what step 2 covers
- [ ] Read any other utility class in `flightpath/util/` with zero test coverage
- [ ] For each untested method: pure logic → write test now; Qt-dependent → note for plan 2; trivial delegation → skip
- [ ] Write targeted tests for all pure-logic methods identified above
