import os
from csvpath.util.log_utility import LogUtility as clout
from csvpath import CsvPath, CsvPaths
from csvpath.util.config import Config
from flightpath.util.file_utility import FileUtility as fiut

class LogUtility:

    @classmethod
    def clear_logging(cls, path:CsvPath|CsvPaths) -> None:
        handlers = path.logger.handlers[:]
        for handler in handlers:
            path.logger.removeHandler(handler)
            handler.close()
        clout.LOGGERS = {}
        path.logger = None

    @classmethod
    def get_log_content(cls, config:Config) -> str:
        logfile = config.get(section="logging", name="log_file")
        log_lines = None
        if os.path.exists(logfile):
            with open( logfile, mode="r", encoding="utf-8") as f:
                log_lines = f.read()
        return log_lines

    @classmethod
    def rotate_log(cls, cwd:str, config:Config) -> None:
        logfile = config.get(section="logging", name="log_file")
        bakdir = os.path.join( cwd, "logs_bak" )
        fiut.move_file_to_numbered( logfile, bakdir )


