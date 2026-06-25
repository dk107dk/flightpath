# Unit Test Coverage Plan 2

Extends coverage to the next layer: API response-parsing logic, State,
TableModel, and the remaining testable methods in CsvpathUtility.

**Scope constraint:** tests only — no production code changes.
**Deferred to Plan 3 (testability refactoring):** workers, Qt dialogs,
KeyUtility, LogUtility (needs real Config), FileCollector.

---

## Step 1 — `test_server_api.py` — `FlightPathServerApi` shared methods ✓

These methods live in `server_api.py` and are inherited by both V1 and V2.
`_to_result` is the highest-value target: it is the single conversion point
from raw HTTP responses to `Result` tuples and runs on every API call.
`httpx.Response(status_code, json=...)` can be constructed directly in tests
without mocking the network.

**Bugs to pin (do not fix — tests-only rule):**
- `discover()` returns a bare tuple on unknown exception (`return (False, ...)`)
  rather than a `Result` — the caller will fail if it tries `.success` on a plain tuple.

### `_to_result`

- [ ] 200 response with JSON body → `Result(True, {...}, None, 200)`
- [ ] 200 response with non-JSON body → `Result(True, <text>, None, 200)`
- [ ] 201 response (created) is also a success → `Result(True, ...)`
- [ ] 299 response is the last success code → `Result(True, ...)`
- [ ] 400 with `"detail"` key in JSON body → error message includes detail text
- [ ] 400 with `"message"` key in JSON body → error message includes message text
- [ ] 400 with no parseable JSON → error message is generic `"Server response: 400"`
- [ ] 500 response → `Result(False, None, ..., 500)`
- [ ] 300 response (redirect) → failure (not in 200–299 range)

### `_url`

- [ ] path without leading slash → `"{host}/{path}"`
- [ ] path with leading slash → leading slash is stripped, no double slash
- [ ] empty path → `"{host}/"`

### `headers` property

- [ ] contains `"access_token"` key (value is key, initially None)
- [ ] contains `"Content-Type": "application/json"`
- [ ] after setting key, `headers["access_token"]` reflects the new value

---

## Step 2 — `test_server_api_v1.py` — V1 result-parsing logic ✓

V1's `download_log` and `get_project_names` have non-trivial logic that
runs after the HTTP call completes. Test by constructing a `V1` instance
directly (bypassing the `__new__` factory) and calling the private HTTP
helpers with patched transport.

The cleanest approach: subclass or mock `_post`/`_get` to return
pre-built `Result` tuples, then assert on the method's output logic.

**Bugs to pin:**

- `get_project_names` calls `Result(True, data["names"], status_code)` — only
  3 args, so `error_message` receives the status code integer and
  `status_code` is `None`. Same bug exists in V2. Pin in tests; fix in Plan 3.

### `download_log`

- [ ] `_post` returns failure → pass-through failure `Result`
- [ ] `_post` returns success, `data` dict has `"file_content"` with valid base64 → decoded string
- [ ] `_post` returns success, `data` dict missing `"file_content"` → `Result(False, None, "Response did not include file_content")`
- [ ] `_post` returns success, `data` is not a dict → `Result(False, None, ...)`
- [ ] `_post` returns success, `"file_content"` is invalid base64 → `Result(False, None, "Could not decode...")`

### `get_project_names`

- [ ] `_post` returns failure → pass-through failure `Result`
- [ ] `_post` returns success, data dict has `"names"` key → `Result.data` is the names list
- [ ] `_post` returns success, data dict missing `"names"` key → `Result(False, None, "Unexpected response...")`
- [ ] Bug pinned: `Result(True, names, status_code)` has 3 args; `error_message` field holds the int status code

---

## Step 3 — `test_server_api_v2.py` — V2 result-parsing logic ✓

**Bug to pin (same download_log issue as V1, plus a new one):**
- V2 `download_log` URL is `"/v2/projects/{name}/files/logs/csvpath.log"` — missing
  the `f` prefix, so `{name}` is never interpolated. The URL is always the literal
  string regardless of the `name` argument.

### `download_log`

- [ ] `_get` returns failure → pass-through
- [ ] `_get` returns success with valid base64 `file_content` → decoded string
- [ ] `_get` returns success, `file_content` missing → failure Result
- [ ] URL bug pinned: `name` is not interpolated (literal `{name}` in URL)

### `download_config`

- [ ] `_get` returns success → `result.data` is `data["value"]` (unwrapped)
- [ ] `_get` returns failure → `Result` is returned unchanged (no unwrap)
- [ ] `_get` returns success but `data` has no `"value"` key → `result.data` is `None`

### `download_env`

- [ ] Same three cases as `download_config`

### `get_project_names` (V2)

- [ ] Same four cases as V1
- [ ] Bug pinned: same 3-arg `Result(True, names, status_code)` misplacement

---

## Step 4 — `test_state.py` — `State` isolated with `tmp_path` ✓

`State` reads/writes `~/.flightpath` and creates directories under `~/FlightPath/`.
Isolation: set `state.state_path` to a `tmp_path` file before any property
access; monkeypatch `pathlib.Path.home` to return `tmp_path` to redirect
`cwd` and directory creation away from the real home directory.

### State file creation

- [ ] New `State()` with no pre-existing file → `data["integrations"]` contains the default list
- [ ] New state file is valid JSON
- [ ] `data` setter with `None` raises `ValueError`

### `data` read/write

- [ ] Write dict, read it back → same content
- [ ] Successive writes → last write wins (no accumulation)

### `current_project`

- [ ] Fresh state with no `current_project` key → defaults to `"Default"`
- [ ] After `current_project = "MyProj"` → `current_project` returns `"MyProj"`
- [ ] Project name with trailing `os.sep` → separator is stripped on read
- [ ] Empty string value → falls back to `"Default"`

### `projects_home`

- [ ] Fresh state → defaults to `"FlightPath"`
- [ ] After setting `projects_home = "MyProjects"` → returns `"MyProjects"`
- [ ] Setting to `None` removes key from state data

### `cwd`

- [ ] Returns `home / projects_home / current_project`
- [ ] Changes when `current_project` changes

### `set_env` / `load_env`

- [ ] `set_env("FOO", "bar")` → `load_env()` sets `os.environ["FOO"] == "bar"`
- [ ] `set_env("FOO", None)` after it was set → key removed from env dict
- [ ] `load_env()` with no env dict in state → no-op, does not raise

### `_change_function_path`

- [ ] `new_config=None` → `ValueError`
- [ ] Valid new config with a functions path → path's dirname added to `sys.path`
- [ ] Switching from old config to new → old dirname removed, new dirname added

---

## Step 5 — `tests/gui/test_table_model.py` — `TableModel` ✓

`TableModel` subclasses `QAbstractTableModel` so requires `qapp`.  The pure
data-manipulation logic is fully testable without rendering.

### Row and column counts

- [ ] Empty data list → `rowCount() == 0`, `columnCount() == 0`
- [ ] Single row of 3 items → `rowCount() == 1`, `columnCount() == 3`
- [ ] Ragged data (rows of different lengths) → `columnCount()` is max row length

### `data_row`

- [ ] Valid index → returns correct row list
- [ ] `index == None` → `ValueError`
- [ ] `index > len(data)` → `ValueError`

### `insertRows`

- [ ] Insert at row 0 → new row appears at index 0; existing data shifts
- [ ] Insert with explicit `new_row_data` → that data appears in the row
- [ ] Insert with `new_row_data=None` → empty-string row sized to current column count
- [ ] `rowCount` increases by 1 after insert

### `insertColumns`

- [ ] Insert at column 0 → all rows gain a new `""` cell at column 0
- [ ] `columnCount` increases by 1 after insert

### `remove_rows`

- [ ] Remove row at valid index → `rowCount` decreases by 1
- [ ] `row < 0` → returns `False`
- [ ] `row + count > rowCount` → returns `False`

### `remove_columns`

- [ ] Remove column at valid index → `columnCount` decreases by 1
- [ ] `column < 0` → returns `False`
- [ ] `column + count > columnCount` → returns `False`

---

## Step 6 — `test_csvpath_utility.py` — remaining `CsvpathUtility` methods ✓

`_add_to_external_comment_of_csvpath_at_position` is already covered in
`test_insert_metadata.py`.  This step covers the remaining methods.

### `_get_char`

- [ ] `"pipe"` → `"|"`
- [ ] `"bar"` → `"|"` (alias)
- [ ] `"comma"` → `","` with any default
- [ ] `"tab"` → `"\t"`
- [ ] `"quotes"` → `'"'`
- [ ] Unknown name → returns the default
- [ ] Name not in `CHAR_NAMES` → returns the default
- [ ] Name mapped to `None` in `CHAR_NAMES` → returns the default

### `get_filepath`

- [ ] Comment with `test-data: /path/to/file.csv` → `"/path/to/file.csv"`
- [ ] Comment with no `test-data` annotation → `None`
- [ ] Empty comment → `None`
- [ ] `None` comment → `None` (guarded at top of method)
- [ ] Path with newline → truncated at newline

### `statement_and_comment`

- [ ] Csvpath string with external comment → returns `(statement, comment)` tuple, both stripped
- [ ] Csvpath string with no comment → comment part is empty string
- [ ] Empty string → returns `("", "")`

### `get_delimiter`

- [ ] Comment with `test-delimiter: pipe` → `"|"`
- [ ] Comment with no `test-delimiter` → `None`

### `get_quotechar`

- [ ] Comment with `test-quotechar: single-quote` → `"'"`
- [ ] Comment with no `test-quotechar` → `None`

---

## Additional bugs found during Step 6

- `_get_char("tab", default)` → `""` not `"\t"`: `c.strip()` strips the tab character; the `None` guard never fires. Pinned in `test_get_char_tab_bug_returns_empty_string`.
- `_get_char("int", default)` → `"int"` not default: `except` block is bare `...`; `c` stays `"int"` and is not `None` so default is skipped. Pinned in `test_get_char_int_bug_returns_literal_int_string`.
- `get_delimiter(None)` and `get_quotechar(None)` → `TypeError`: both pass `None` directly to `get_metadata()` unlike `get_filepath` which guards against it. Pinned in respective None tests.
- Comment format note: `get_filepath`/`get_delimiter`/`get_quotechar` expect inner comment text (no `~` markers). Passing raw csvpath string with markers includes the trailing `~` in extracted values.

All six bugs added to memory: `project_missing_none_guards.md`.

## After all steps: full suite regression check

```bash
QT_QPA_PLATFORM=offscreen poetry run python -m pytest -v
```

All existing tests (plan 1 + GUI suite) must continue to pass.
