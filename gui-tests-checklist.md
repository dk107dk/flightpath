# FlightPath Data GUI Test Checklist

## June 2026 Release

`[x]` = covered by pytest-qt suite &nbsp;|&nbsp; `[ ]` = manual / not yet automated

Coverage annotations show the test file(s) and function name(s) for each automated item.

---

### HOME

- [✓] new project — combo creates project, cancel keeps current
  - `test_new_project_workflow.py`:
		✓`test_new_project_create_end_to_end`,
		✓`test_new_project_cancel_keeps_current_project`
- [✓] correct editors open
  - [✓] CsvPath — `.csvpath` / `.csvpaths` → CsvpathViewer`
    - test_open_file.py`: `test_open_csvpath_file_opens_csvpath_viewer`
  - [✓] JSON — `.json` → JsonViewer2
    - `test_open_file.py`: `test_open_json_file_opens_json_viewer`
  - [✓] JSONL — `.jsonl` → DataViewer (grid); "Edit as JSON" → JsonViewer2
    - `test_save_as.py`: `test_jsonl_grid_save_redirects_to_csv` *(opens JSONL in DataViewer)*
    - `test_open_file.py`: `test_open_jsonl_as_json` *("Edit as JSON" → JsonViewer2)*
    - `test_manifest_json_viewer.py`: `test_manifest_json_editable_opens_in_json_viewer2`
  - [✓] Grid: CSV — `.csv` → DataViewer
    - `test_open_file.py`: `test_open_csv_file_opens_data_viewer`
  - [✓] Grid: XLSX — `.xlsx` → DataViewer; data content verified against CPI file
    - `test_xlsx_save_as.py`:
		`test_xlsx_opens_in_data_viewer`,
		`test_xlsx_worksheet_has_correct_row_count`
  - [✓] Raw — toggle from grid view to raw text view
    - `test_content_actions.py`: `test_toggle_raw_view_on_csv`
  - [✓] Markdown — `.md` → MdViewer
    - `test_open_file.py`: `test_open_md_file_opens_md_viewer`
  - [✓] Metadata grid — file manifest.json from right-side helper windows is shown in a JSON grid view (JsonViewer)
    - `test_manifest_json_viewer.py`:
		✓`test_named_file_manifest_opens_in_json_viewer`,
		✓`test_named_file_manifest_json_viewer_has_rows`,
        ✓`test_named_paths_manifest_opens_in_json_viewer`,
		✓`test_regular_json_opens_in_json_viewer2`
- [✓] Ops, AI, Help tabs in right-hand column appear when a file is shown
  - `test_right_column_tabs.py`:
		✓`test_rt_tabs_appear_after_csv_open`,
		✓`test_rt_tabs_appear_after_xlsx_open`,
		✓`test_rt_tabs_appear_after_jsonl_open`,
		✓`test_rt_tabs_appear_after_json_open`,
        ✓`test_rt_tabs_appear_after_md_open`,
		✓`test_rt_tabs_appear_after_csvpath_open`,
		✓`test_rt_tabs_hide_on_welcome_screen`,
		✓`test_rt_tabs_hide_when_last_tab_closed`
- [✓] copy data in / open project dir — welcome button opens project directory in Finder
  - `test_welcome_buttons.py`: `test_copy_in_button_opens_project_dir`
- [x] one-off run
  - [✓] result tabs appear — Printouts, Log, Errors, Matches, Variables, Code, Why
    - `test_one_off_run.py`: `test_one_off_run_creates_result_tabs`
  - [✓] Matches tab contains a DataViewer with data
    - `test_one_off_run.py`: `test_one_off_run_matches_tab_has_data`
  - [✓] save result tab using rt-click "Save as" — writes CSV to project dir
    - `test_one_off_run.py`: `test_one_off_run_save_matches_writes_csv`
  - [✓] "What am I seeing?" tab present (objectName "Why")
    - `test_one_off_run.py`: `test_one_off_run_creates_result_tabs`
- [✓] welcome buttons don't blow up — run/find-data disabled in empty project; configure AI, reload, copy-in work
  - `test_welcome_buttons.py`:
		✓`test_run_button_disabled_in_empty_project`,
		✓`test_find_data_button_disabled_in_empty_project`,
		✓`test_configure_ai_button_switches_to_config`,
		✓`test_reload_button_stays_on_welcome`,
		✓`test_copy_in_button_opens_project_dir`
- [✓] open file — `read_validate_and_display_file_for_path` routes to correct viewer
  - `test_open_file.py`:
		✓`test_open_csvpath_file_opens_csvpath_viewer`,
		✓`test_open_csv_file_opens_data_viewer`,
		✓`test_open_json_file_opens_json_viewer`,
		✓`test_open_md_file_opens_md_viewer`,
		✓`test_open_jsonl_as_json`
  - [✓] open XLSX with multiple worksheets — worksheet selector tab appears
    - `test_xlsx_save_as.py`:
		✓`test_xlsx_worksheets_for_path_returns_sheet_names`,
		✓`test_xlsx_named_worksheet_opens_in_data_viewer`,
		✓`test_xlsx_two_worksheets_open_as_separate_tabs`
- [x] file operations (sidebar context menu + keyboard)
  - [✓] delete file — confirm removes, cancel keeps
    - `test_sidebar_context_menu.py`:
		✓`test_delete_file_yes_removes_file`,
		✓`test_delete_file_no_keeps_file`,
		✓`test_delete_directory_yes_removes_dir`,
		✓`test_delete_directory_no_keeps_dir`,
		✓`test_delete_selected_file_shows_welcome`
  - [x] copy + paste file (deconflicted name)
    - `test_file_operations.py`: `test_copy_paste_creates_duplicate`
  - [x] rename file — confirm renames, cancel reverts
    - `test_file_operations.py`: `test_rename_file`, `test_rename_cancel_keeps_file`
  - [x] new file — creates CSV, csvpath, JSON, MD with starter content
    - `test_sidebar_context_menu.py`:
		✓`test_new_csv_file_creates_file`,
		✓`test_new_md_file_creates_file`,
		✓`test_new_csvpath_file_creates_file`,
		✓`test_new_json_file_creates_file`
  - [x] new JSONL file — creates `.jsonl` with starter content
    - `test_sidebar_context_menu.py`:
		`test_new_jsonl_file_creates_file_with_object`, 		`test_new_jsonl_file_creates_file_with_array`
  - [x] cut + paste file
    - `test_file_operations.py`: `test_cut_paste_moves_file`
  - [x] right-click on whitespace in project tree — shows root-level context menu
    - `test_whitespace_context_menu.py`:
		`test_whitespace_menu_has_new_file_action`,
		`test_whitespace_menu_has_new_folder_action`,
		`test_whitespace_menu_has_open_project_dir_action`,
		`test_whitespace_menu_has_paste_action`,
		`test_whitespace_menu_paste_disabled_when_clipboard_empty`,
		`test_whitespace_menu_excludes_delete_action`,
		`test_whitespace_menu_excludes_rename_action`,
		`test_whitespace_menu_excludes_save_file_action`
- [x] save and save-as
  - [x] csvpath — in-place save writes changes to disk
    - `test_save_as.py`: `test_csvpath_save_writes_changes`
  - [x] JSON — in-place save (JsonViewer2); save-as to new path
    - `test_save_as.py`:
		`test_json_viewer_save_writes_changes`,
		`test_json_viewer_save_as_new_file`
  - [x] JSONL — save in JsonViewer2 preserves JSONL line format
    - `test_save_as.py`: `test_jsonl_json_viewer_save_preserves_jsonl_format`
  - [x] grid/CSV — save-as with comma delimiter
    - `test_save_as.py`: `test_csv_save_as_comma_delimiter`
  - [x] grid/CSV — save-as with pipe delimiter; output has `|` not `,`
    - `test_save_as.py`: `test_csv_save_as_pipe_delimiter`
  - [x] XLSX — on_save() redirects to save-as dialog (can't save back as XLSX)
    - `test_xlsx_save_as.py`: `test_xlsx_save_redirects_to_save_as`
  - [x] XLSX — save-as comma CSV; save-as pipe PSV
    - `test_xlsx_save_as.py`:
		`test_xlsx_save_as_comma_csv`,
		`test_xlsx_save_as_pipe_delimited`
  - [x] JSONL in grid — on_save() redirects to save-as CSV
    - `test_save_as.py`: `test_jsonl_grid_save_redirects_to_csv`
  - [x] save-as with single-quote quotechar
    - `test_save_as.py`: `test_csv_save_as_single_quote_quotechar`
  - [x] JSON save-as — prompts for path via input2 dialog
    - `test_save_as.py`: `test_json_viewer_save_as_triggers_input2_dialog`
- [x] file content ops: cut, copy, paste inside editors
  - [x] cut in text editors (csvpath, MD, JSON)
    - `test_content_copy_paste.py`:
		`test_csvpath_editor_cut_clears_editor`,
		`test_json_editor_cut_clears_editor`
  - [x] copy lines in grid
    - `test_content_copy_paste.py`:
		`test_grid_copy_single_cell`,
		`test_grid_copy_rectangular_selection`
  - [x] copy irregular cell selection in grid
    - `test_content_copy_paste.py`: `test_grid_copy_irregular_selection`
  - [x] paste in grid
    - `test_content_copy_paste.py`: `test_grid_paste_single_cell`, `test_grid_paste_multi_cell`
  - [x] paste-as-new in grid (creates deconflicted copy)
    - `test_content_copy_paste.py`: `test_grid_paste_as_new_creates_csv`
- [x] data toolbar
  - [x] toggle raw view
    - `test_content_actions.py`: `test_toggle_raw_view_on_csv`
  - [x] file info — FileInfo tab added to helper panel
    - `test_content_actions.py`: `test_file_info_opens_info_tab`
  - [x] data sampling — changing rows combo triggers worker reload
    - `test_content_actions.py`: `test_data_sampling_reloads_file`
  - [x] random sample — random sampling mode produces different rows
    - `test_content_actions.py`:
		`test_random_sampling_produces_different_rows`,
		`test_random_sample_zero_triggers_reload`,
		`test_random_sample_all_triggers_reload`
  - [x] save sample (Matches tab rt-click → CSV written to project dir)
    - `test_one_off_run.py`: `test_one_off_run_save_matches_writes_csv`
  - [x] set delimiter to view — toolbar delimiter changes how grid parses file
    - `test_content_actions.py`: `test_delimiter_change_affects_column_count`
- [x] create directory
  - `test_sidebar_context_menu.py`: `test_new_folder_creates_directory`
- [x] create files — CSV, csvpath, JSON, MD (starter content verified)
  - `test_sidebar_context_menu.py`:
		✓`test_new_csv_file_creates_file`,
		✓`test_new_md_file_creates_file`,
		✓`test_new_csvpath_file_creates_file`,
		✓`test_new_json_file_creates_file`
  - [x] create JSONL file
    - `test_sidebar_context_menu.py`:
		`test_new_jsonl_file_creates_file_with_object`,
		`test_new_jsonl_file_creates_file_with_array`
- [x] permanent delete
  - [x] left sidebar: delete directory
    - `test_sidebar_context_menu.py`:
		`test_delete_directory_yes_removes_dir`,
		`test_delete_directory_no_keeps_dir`
  - [x] right ops panel: named-files dir removed and sidebar rebuilt
    - `test_permanent_delete.py`: `test_permanent_delete_named_file`
    - `test_right_sidebar_refresh.py`:
		`test_named_files_refresh_replaces_view`,
		`test_named_files_refresh_picks_up_new_entry`
  - [x] right ops panel: named-paths dir removed and sidebar rebuilt
    - `test_permanent_delete.py`: `test_permanent_delete_named_paths`
    - `test_right_sidebar_refresh.py`:
		`test_named_paths_refresh_replaces_view`,
		`test_named_paths_refresh_picks_up_new_entry`
  - [x] right ops panel: archive result dir removed and sidebar rebuilt
    - `test_permanent_delete.py`: `test_permanent_delete_archive_result`
    - `test_right_sidebar_refresh.py`: `test_archive_refresh_replaces_view`
- [x] uneditable files:
  - [x] tinted green
    - `test_uneditable_tint_and_copy_back.py`:
		`test_data_viewer_uneditable_tinted`,
		`test_json_viewer_uneditable_tinted`,
		`test_json_viewer2_uneditable_tinted`,
		`test_csvpath_viewer_uneditable_tinted`,
		`test_data_viewer_editable_not_tinted`
  - [x] copy-back prompt on right window files
    - `test_uneditable_tint_and_copy_back.py`:
		`test_data_viewer_on_save_prompts_copy_back`,
		`test_json_viewer_context_menu_prompts_copy_back`,
		`test_json_viewer2_context_menu_prompts_copy_back`,
		`test_copy_back_yes_copies_manifest_to_project`,
		`test_copy_back_yes_copies_csv_to_project`


---

### EXAMPLES

- [x] run through the examples — open each example csvpath, run it, check result tabs
  - `test_examples.py`: `test_example_run_creates_log_and_why_tabs`
- [x] large file warning — open `dups.csvpaths` (> 1,000,000b threshold) triggers warning dialog
  - `test_examples.py`: `test_large_file_triggers_warning_dialog`
- [x] auto-add `test-data:` path directive — one-off run on csvpath without test-data: prompts to add it
  - `test_examples.py`: `test_run_without_test_data_adds_directive_to_editor`

---

### DIALOGS

- [x] stage data — register a named-file via the Stage Data dialog
  - [x] stage a single file
    - `test_stage_and_load.py`:
		`test_stage_single_file_registers_named_file`,
		`test_stage_single_file_sidebar_refreshes`
  - [x] stage a directory
    - `test_stage_and_load.py`: `test_stage_directory_registers_multiple_named_files`
  - [x] set template on a named-file
    - `test_settings_dialogs.py`: `test_files_template_dialog_saves_template`
  - [x] set activation on a named-file
    - `test_settings_dialogs.py`: `test_activation_dialog_saves_on_arrival`
  - [x] set SFTP servers on a named-file
    - `test_settings_dialogs.py`: `test_sftp_dialog_opens_for_named_file`
- [x] load csvpaths — register a named-paths group via the Load Csvpaths dialog
  - [x] load from a `.csvpath` / `.csvpaths` file
    - `test_stage_and_load.py`: `test_load_csvpath_file_creates_named_paths_group`
  - [x] load from a directory of csvpath files
    - `test_stage_and_load.py`: `test_load_csvpaths_directory_creates_named_paths_group`
  - [x] load from a JSON definition file (when well-formed)
    - `test_stage_and_load.py`: `test_load_json_definition_creates_named_paths_groups`
  - [x] load from malformed JSON — errors show in errors form
    - `test_stage_and_load.py`: `test_load_malformed_json_shows_error`
  - [x] overwrite existing definition (copy-back flow)
    - `test_stage_and_load.py`:
		`test_load_dialog_shows_overwrite_button_for_existing_name`,
		`test_overwrite_existing_named_paths_succeeds`
  - [x] set template on a named-paths group
    - `test_stage_and_load.py`: `test_load_csvpath_file_with_template_stores_template`
    - `test_settings_dialogs.py`: `test_paths_template_dialog_saves_template`
  - [x] set webhooks on a named-paths group
    - `test_settings_dialogs.py`: `test_webhooks_dialog_saves_url`
- [x] production run (run groups) — `collect_paths` via `main.run_paths()`
  - [x] Log tab created after run completes (objectName `Log-<cid>`)
    - `test_production_run.py`: `test_production_run_creates_log_tab`
  - [x] Log tab QPlainTextEdit has content
    - `test_production_run.py`: `test_production_run_log_tab_has_content`
  - [x] archive directory populated after run
    - `test_production_run.py`: `test_production_run_archive_populated`
  - [x] runs tab in Ops panel shows the run
    - `test_production_run.py`: `test_production_run_adds_item_to_runs_accordion`
  - [x] after-run info dialog appears (or is suppressed in headless)
    - `test_production_run.py`: `test_info_dialog_appears_on_info_icon_click`
  - [ ] mid-run info dialog (long-running csvpath)
  - [x] click archive entry → opens result files in content panel
    - `test_production_run.py`: `test_archive_file_click_opens_content_tab`
  - [x] rerun — re-executes the same named-paths group
    - `test_production_run.py`: `test_rerun_produces_second_log_tab`
  - [x] run with bad template → RunFailedDialog shown
    - `test_production_run.py`: `test_bad_template_shows_run_failed_dialog`
  - [ ] activation fires after run (if activation is set)
  - [ ] webhooks execute after run (if webhooks configured)
- [x] find data dialog
  - [x] find files — search returns matching named-file entries
    - `test_find_data.py`:
		`test_find_files_populates_table`,
		`test_find_files_table_has_date_and_path_columns`
  - [x] find results — search returns matching archive entries
    - `test_find_data.py`: `test_find_results_populates_table`
  - [x] show metadata and data — clicking a result opens a content tab
    - `test_find_data.py`: `test_open_files_file_opens_content_tab`
  - [x] welcome page "Find data" button opens dialog without error
    - `test_find_data.py`:
		`test_welcome_find_data_button_opens_dialog`,
		`test_welcome_find_data_button_enabled_after_registration`

---

### CONFIG

- [x] config panel opens (configure AI welcome button → Config view)
  - `test_config.py`: `test_open_config_switches_to_config_view`
  - `test_welcome_buttons.py`: `test_configure_ai_button_switches_to_config`
- [x] save changes persist to `config.ini` on disk
  - `test_config.py`: `test_save_config_persists_value_to_ini`
- [x] save repopulates form fields from saved values
  - `test_config.py`: `test_save_config_repopulates_form`
- [x] cancel reverts unsaved changes
  - `test_config.py`: `test_cancel_config_reverts_value`
- [x] save → close → reopen — values survive close/reopen cycle (full restart requires process isolation)
  - `test_config_forms.py`: `test_values_survive_close_reopen`
- [x] cache section — cache controls work (use_cache toggle)
  - `test_config_forms.py`: `test_cache_use_cache_toggle_saved`
- [ ] config form — all form fields render and accept input
- [ ] env section
  - [x] add env.json var — variable appears in substitutions
    - `test_config_forms.py`:
		`test_env_form_add_var_appears_in_envs`,
		`test_env_form_add_fields_cleared_after_add`
  - [x] env.json var sub visible in actuals panel
    - `test_env_form.py`:
		`test_env_form_add_var_appears_in_table`, 		`test_env_form_added_var_value_is_correct`,
		`test_env_form_filter_limits_displayed_vars`, 		`test_env_form_empty_filter_shows_all_vars`,
		`test_env_form_delete_var_by_empty_value`
  - [x] switch env.json → env — actuals shows no substitution available
    - `test_env_form.py`: `test_env_form_os_source_shows_os_environ_vars`
  - [x] switch back to env.json — full path auto-populated
    - `test_env_form.py`:
		`test_config_form_var_sub_source_auto_completes_to_json`,
		`test_config_form_var_sub_source_env_string_preserved`
- [x] logging section — log file size saved and applied
  - `test_config_forms.py`:
		`test_logging_form_saves_log_file_size`,
		`test_logging_form_repopulates_after_save`
- [x] extensions section — custom extensions accepted
  - `test_config_forms.py`: `test_extensions_form_saves_csv_extensions`
- [x] errors section — error pattern saved
  - `test_config_forms.py`: `test_errors_form_saves_pattern`
- [x] inputs section — named-files / named-paths paths saved
  - `test_config_forms.py`:
		`test_inputs_form_saves_named_files_path`,
		`test_inputs_form_saves_named_paths_path`
- [x] results section — archive path saved
  - `test_config_forms.py`: `test_results_form_saves_archive_path`
- [x] offsets section — offset values saved
  - `test_offsets_form.py`:
		`test_offsets_form_now_label_shows_todays_date`,
		`test_offsets_form_days_offset_advances_date`,
		`test_offsets_form_months_offset_advances_date`,
		`test_offsets_form_years_offset_advances_date`,
		`test_offsets_form_on_set_writes_daut_class_attributes`,
		`test_offsets_form_negative_offset_moves_date_back`,
		`test_offsets_form_invalid_input_clears_field`,
		`test_offsets_form_on_reset_zeros_class_attributes`
- [x] project form — project-level metadata saved
  - `test_projects_form.py`:
		`test_projects_form_displays_projects_home`,
		`test_projects_form_field_is_read_only`,
		`test_projects_form_add_to_config_preserves_projects_home`,
		`test_projects_form_populate_refreshes_display`
- [ ] functions section
  - [x] register a custom function — appears in function list
    - `test_functions_form.py`:
		`test_functions_form_imports_path_saved_to_config`,
		`test_functions_form_imports_path_restored_on_populate`,
		`test_functions_form_actuals_table_shows_imports_field`,
		`test_functions_form_actuals_table_shows_imports_value`,
		`test_functions_form_reload_skipped_for_empty_path`,
		`test_functions_form_reload_calls_factory_with_path`
- [x] integrations tab
  - [x] select groups — group selections saved
    - `test_integrations_form.py`:
		`test_listeners_groups_saved_to_config`,
		`test_listeners_groups_restored_on_populate`,
		`test_listener_name_click_appends_group`,
		`test_listener_name_click_does_not_duplicate`
  - [x] FTP setup — FTP connection fields saved
    - `test_integrations_form.py`:
		`test_sftp_all_fields_saved_to_config`,
		`test_sftp_all_fields_restored_on_populate`
  - *Additional integrations coverage (not separate checklist items):*
    - `test_integrations_form.py`:
		`test_otlp_fields_saved_to_os_environ`,
		`test_otlp_populate_reads_from_os_environ`,
		`test_openlineage_all_fields_saved_to_config`,
		`test_openlineage_all_fields_restored_on_populate`,
		`test_sqlite_db_path_saved_to_config`,
		`test_sqlite_db_path_restored_on_populate`,
		`test_sqlite_db_created_after_run`,
		`test_slack_webhook_url_roundtrip`,
		`test_ckan_fields_roundtrip`,
		`test_sql_tab_fields_roundtrip`
- [ ] LLM / AI section
  - [ ] AI config warning shown on AI tab when not configured
  - [ ] open metadata dir — opens dir in Finder
    - `test_llm_form.py`: `test_llm_open_metadata_dir_does_not_crash` *(smoke test only — Finder open is monkeypatched)*
  - [x] open generator.ini — opens file in content panel
    - `test_llm_form.py`: `test_llm_open_ai_config_calls_open_file`
  - [x] generator.ini path displayed correctly
    - `test_llm_form.py`:
		`test_llm_generator_ini_path_displayed`,
		`test_llm_generator_ini_path_in_config_dir`
  - [x] "use for all projects" — setting propagates to other projects
    - `test_llm_form.py`:
		`test_llm_checkbox_checked_writes_to_state`,
		`test_llm_checkbox_unchecked_does_not_write_to_state`,
		`test_llm_populate_falls_back_to_state_when_config_empty`,
		`test_llm_checkbox_checked_when_config_matches_state`,
		`test_llm_checkbox_unchecked_when_config_differs_from_state`
  - *Additional LLM coverage (field round-trips):*
    - `test_llm_form.py`:
		`test_llm_fields_saved_to_config`,
		`test_llm_fields_restored_on_populate_from_config`,
		`test_llm_fields_strip_whitespace_on_save`,
		`test_llm_actuals_table_shows_all_three_fields`,
		`test_llm_actuals_table_shows_saved_model_value`

---

### SERVER PANEL

> Automated: mock-tier (no server) + live_server subprocess tier. See `test_server_form.py`.

- [ ] API docs link opens
- [x] setup server (host/port entry)
  - `test_server_form.py`:
		`test_server_form_saves_host_and_key`,
 		`test_server_form_populates_from_config`,
		`test_live_server_is_reachable`
- [ ] create new key — key displayed in dialog
- [x] create project
  - `test_server_form.py`:
		`test_get_project_names_populates_list`,
		`test_create_project_calls_api`,
		`test_live_create_and_list_project`
- [x] upload config
  - `test_server_form.py`:
 		`test_upload_config_answer_yes_calls_api`,
		`test_upload_config_answer_no_skips_api`,
		`test_upload_config_shows_warning_on_api_failure`,
		`test_live_upload_and_download_config_round_trip`
- [ ] sync config
- [x] download config
  - `test_server_form.py`:
		`test_download_config_writes_file`,
		`test_download_config_shows_warning_on_failure`,
		`test_live_upload_and_download_config_round_trip`
- [x] download env
  - `test_server_form.py`:
		`test_download_env_writes_file`,
		`test_live_upload_and_download_env_round_trip`
- [ ] sync env
- [ ] shutdown server
  - `test_server_form.py`:
		`test_server_form_shutdown_button_disabled_without_credentials`,
		`test_server_form_shutdown_button_enabled_with_credentials`,
		`test_shutdown_answer_yes_calls_api`
			*(button state + API call covered; full server shutdown requires live server)*

---

### DARK MODE

- [ ] dark mode — app renders correctly in dark OS theme
- [ ] switch OS theme — app responds to system theme change

---

### SERVER API

> Requires running FlightPath Server.

- [ ] all API endpoint tests pass
- [ ] download logs

---

### BACKENDS

> Cloud/SFTP backends require credentials and network access — manual or CI with secrets.

- [ ] S3 — upload and download round-trip
- [ ] SFTP — upload and download round-trip
- [ ] Azure Blob — upload and download round-trip
- [ ] GCS — upload and download round-trip
- [ ] helper window titles include backend name

---

### AI

> Requires LLM API key configured in `[llm]` section — manual or CI with secrets.

- [ ] Explain a csvpath — AI tab returns explanation
- [ ] Create a csvpath from data — generated csvpath is valid
- [ ] Answer a csvpath question — AI tab returns answer
- [ ] Create data from a csvpath — generated test data matches schema
