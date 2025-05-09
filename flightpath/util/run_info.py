from csvpath import CsvPath

class RunInfo:

    def __init__(self, path:CsvPath) -> None:
        self.path = path
        self.info = {}
        self.populate(path)

    def populate(self, path:CsvPath) -> None:
        self.info["identity"] = path.identity
        self.info["filename"] = path.scanner.filename
        self.info["scan_count"] = path.scan_count
        self.info["match_count"] = path.match_count
        self.info["skip_blank_lines"] = path.skip_blank_lines
        self.info["delimiter"] = "," if path.delimiter is None else path.delimiter
        self.info["quotechar"] = '"' if path.quotechar is None else path.quotechar
        self.info["collecting"] = path.collecting
        self.info["error_format"] = path.config.get(section="errors", name="pattern")
        self.info["csvpath_log_level"] = path.config.csvpath_log_level
        self.info["csvpath_errors_policy"] = path.config.csvpath_errors_policy
        self.info["stop_on_validation_errors"] = path.stop_on_validation_errors
        self.info["fail_on_validation_errors"] = path.fail_on_validation_errors
        self.info["print_validation_errors"] = path.print_validation_errors
        self.info["log_validation_errors"] = path.log_validation_errors
        self.info["raise_validation_errors"] = path.raise_validation_errors
        self.info["match_validation_errors"] = path.match_validation_errors
        self.info["collect_validation_errors"] = path.collect_validation_errors
        self.info["explain"] = path.explain
        self.info["collect_when_not_matched"] = path.collect_when_not_matched
        self.info["stopped"] = path.stopped
        self.info["is_valid"] = path.is_valid
        self.info["logic_mode"] = path.logic_mode
        self.info["print_mode"] = path.print_mode
        self.info["printers"] = path.printers
        self.info["will_run"] = path.will_run
        self.info["unmatched_mode"] = path.unmatched_mode
        self.info["data_from_preceding"] = path.data_from_preceding

