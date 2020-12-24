"""
Simple logging config module. I fully expect this to change a little to have
racetrack functional using /build/trees/nsx-dev-testing/racetrack
"""

import logging
import logging.handlers
import os
import sys
import time
import traceback

from lib import params


class Log:
    def __init__(self, logger):
        self.logger = logger

    def fmt_args(self, fmt, args):
        if not isinstance(fmt, str):
            fmt = repr(fmt)
        args_list = []
        for arg in args:
            try:
                str(arg)
                args_list.append(arg)
            except Exception as fault:
                args_list.append(repr(arg))
        args = tuple(args_list)
        return fmt, args

    def debug(self, fmt, *args):
        fmt, args = self.fmt_args(fmt, args)
        self.logger.debug(fmt % args)

    def info(self, fmt, *args):
        fmt, args = self.fmt_args(fmt, args)
        self.logger.info(fmt % args)

    def warn(self, fmt, *args):
        fmt, args = self.fmt_args(fmt, args)
        self.logger.warn(fmt % args)

    def error(self, fmt, *args):
        fmt, args = self.fmt_args(fmt, args)
        self.logger.error(fmt % args)

    def traceback(self, fault):
        msg = "Error %s:%s. Traceback -" % (str(fault.__class__), str(fault))
        msg += "".join(traceback.format_exception(*sys.exc_info()))
        self.logger.error("%s", msg)


def get_logger(
    console_log_level="DEBUG",
    file_log_filename="test_runner.log",
    file_log_level="DEBUG",
    file_log_max_bytes=1_000_000,
    file_log_backup_count=5,
):
    """ provides console and file loggers """
    log_dir = ROOT_DIR + os.path.sep + "logs"

    file_log_filepath = os.path.join(log_dir, file_log_filename)

    formatter = logging.Formatter(params.LOG_FORMAT)
    formatter.converter = time.gmtime  # log UTC timestamps

    log = logging.getLogger("root")
    log.setLevel(logging.DEBUG)

    console_handler = logging.StreamHandler(sys.stdout)
    file_handler = logging.handlers.RotatingFileHandler(
        file_log_filepath, maxBytes=file_log_max_bytes, backupCount=file_log_backup_count
    )
    formatter = logging.Formatter(params.LOG_FORMAT, datefmt=params.LOG_DATE_FORMAT)
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)

    console_handler.flush = sys.stdout.flush

    if os.path.isfile(file_log_filepath) and os.path.getsize(file_log_filepath) > 0:
        file_handler.doRollover()  # Recycle log name: .1 -> .2, ..., .max_logs

    console_handler.setLevel(console_log_level)
    file_handler.setLevel(file_log_level)

    log.addHandler(console_handler)
    log.addHandler(file_handler)

    return log
