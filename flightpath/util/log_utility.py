import os
import logging
from csvpath.util.log_utility import LogUtility as clout
from csvpath import CsvPath, CsvPaths
from csvpath.util.config import Config
from flightpath.util.file_utility import FileUtility as fiut
from flightpath.util.state import State

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


    #
    # setup a FP-specific logger
    #

    @classmethod
    def logger(cls, state:State):
        logger = None
        log_file_handler = None
        filename = os.path.join(state.cwd, "logs")
        filename = os.path.join(filename, "flightpath.log")
        log_file_handler = logging.FileHandler(
            #
            # put log in a log dir of the current project. that may not be where the
            # CsvPath logger writes, but we're not expected to run FlightPath logging
            # except in unusual cases or development.
            #
            filename,
            encoding="utf-8",
        )
        formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
        )
        log_file_handler.setFormatter(formatter)
        logger = logging.getLogger("flightpath")
        logger.addHandler(log_file_handler)
        logger.setLevel(logging.DEBUG)
        return logger

