import logging
from . import Context
import os

LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


class Logger(object):
    def __init__(self):
        self.logger = logging.getLogger("chariot")
        self.console = None
        self.file_log = None

    def log_init(self, log_level="INFO", log_file=None):
        self.console = logging.StreamHandler()
        self.console.setLevel(getattr(logging, log_level))

        fmt = logging.Formatter('[%(levelname)s] %(message)s')
        self.console.setFormatter(fmt)

        self.logger.addHandler(self.console)
        self.logger.setLevel(getattr(logging, log_level))

        if log_file is not None:
            self.file_log = logging.FileHandler(log_file)
            self.file_log.setLevel(getattr(logging, log_level))
            fmt = logging.Formatter('[%(levelname)s] %(asctime)s  %(filename)s %(lineno)d :\n %(message)s')
            self.file_log.setFormatter(fmt)
            self.logger.addHandler(self.file_log)

        Context.logger = self.logger

    def log_reinit(self, log_level="INFO", log_file=None):
        self.logger.removeHandler(self.console)
        if self.file_log is not None:
            self.logger.removeHandler(self.file_log)
        self.log_init(log_level, log_file)


logger = Logger()
logger.log_init()


def log_reinit():
    log_file = os.path.join(Context.log_path, "main.log")
    logger.log_reinit(Context.log_level, log_file)
