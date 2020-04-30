"""
Simple logging config module. I fully expect this to change a little to have
racetrack functional using /build/trees/nsx-dev-testing/racetrack
"""
import inspect
import logging
import logging.handlers
import os
import sys
import time

FORMAT = ('%(asctime)s %(levelname)s %(name)s'
          '[%(lineno)d]:%(funcName)s %(message)s')

log = logging.getLogger(__name__)

plugin_name = "MJOLNIR::"

class SummaryLogFilter(logging.Filter):
    def filter(self, record):
        if record.levelno >= logging.WARNING:
            return False
        return getattr(record, "summary", False)


def banner(self, message, *args, **kwargs):
    """
    Banner level messages will be surrounded by dashes ('-'),
    and sent to Racetrack (if configured).

    The logging level may be specified via the keyword argument 'level'
    """
    level = getattr(logging, kwargs.pop("level", "INFO"))
    if self.isEnabledFor(level):
        msg = message % args
        kwargs.setdefault("extra", {})["summary"] = True
        self._log(level, "-" * len(msg), ())
        self._log(level, msg, (), **kwargs)
        self._log(level, "-" * len(msg), ())


logging.Logger.banner = banner


class CustomLogFilter(logging.Filter):
    def __init__(self, excludeModules=None, excludeFiles=None,
                 excludeMethods=None):
        self.excludeModules = excludeModules or []
        self.excludeFiles = excludeFiles or []
        self.excludeMethods = excludeMethods or []
        logging.Filter.__init__(self)

    def filter(self, record):
        if (record.module in self.excludeModules or
                record.filename in self.excludeFiles or
                record.funcName in self.excludeMethods):
            return False
        return True


if not hasattr(logging.Logger, 'verify'):
    # vmware.pytest_traditions.racetrack monkey pacthes the logger class to
    # provide a nice interface for posting Racetrack verifications. When we
    # aren't running with racetrack we still want existing log.verify(...)
    # calls to succeed (albeit without posting to racetrack).
    _NOT_SET = object()

    def verify(self, msg, actual, expected, result=_NOT_SET, file_path=None):
        if result is _NOT_SET:
            result = actual == expected
        method = self.info if result else self.warning
        fmt = 'Verification - %s: %s. Actual: %s Expected: %s'
        return method(fmt, msg, 'PASS' if result else 'FAIL', actual, expected)

    logging.Logger.verify = verify


class NameAdapter(logging.LoggerAdapter):
    """
    Prepends '[self.name] ' to the logged message, where self is taken from
    the scope where log.xxx was called. If there's no self in that scope or
    self.name is None, then the message will remain unchanged.

    https://docs.python.org/2/howto/logging-cookbook.html

    NOTE: sys._getframe is CPython specific (overhead: ~5 us)
    """
    warn = logging.LoggerAdapter.warning

    def process(self, msg, kwargs):
        try:
            name = sys._getframe(2).f_locals['self'].name
        except (ValueError, KeyError, AttributeError):
            pass
        else:
            if name:
                msg = '[%s] %s' % (name, msg)
        return msg, kwargs

    def banner(self, *args, **kwargs):
        return self.logger.banner(*args, **kwargs)

    def verify(self, *args, **kwargs):
        # Monkey-patched by vmware.pytest_traditions.racetrack
        return self.logger.verify(*args, **kwargs)


def setup_logging(module_name, lookup_self_name=True):
    """Entry point for systest logging

    lookup_self_name: bool
      Prepend the message with '[self.name] ' when logging within a class
      and the self.name attribute is set

    usage:
      log = setup_logging(__name__)  # module level
    """
    if module_name == '__main__':
        # Try to find the proper module name when running scripts
        module = inspect.getmodule(inspect.currentframe().f_back)
        loader = getattr(module, '__loader__', None)
        if loader:
            module_name = loader.fullname
            log.info("changing logger name '__main__' to %r in %s",
                     module_name, module.__file__)

    logger = logging.getLogger(module_name)
    if lookup_self_name:
        return NameAdapter(logger, {})
    return logger


def log_to_stdout(level=None):
    """Helper to add logging to stdout in standalone scripts"""
    formatter = logging.Formatter(FORMAT)
    formatter.converter = time.gmtime  # log UTC timestamps

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root = logging.getLogger()
    if level is not None:
        if isinstance(level, str):
            level = getattr(logging, level)
        handler.setLevel(level)
    root.addHandler(handler)


def log_to_file(filename, level="DEBUG", max_logs=9):
    """Setup a rotating file handler under <filename>"""
    path = os.path.abspath(filename)

    formatter = logging.Formatter(FORMAT)
    formatter.converter = time.gmtime  # log UTC timestamps

    handler = logging.handlers.RotatingFileHandler(path, backupCount=max_logs)
    handler.setFormatter(formatter)
    handler.set_name('rotating_handler')

    if os.path.isfile(path) and os.path.getsize(path) > 0:
        handler.doRollover()  # Recycle log name: .1 -> .2, ..., .max_logs

    root = logging.getLogger()
    if level is not None:
        if isinstance(level, str):
            level = getattr(logging, level)
        root.setLevel(level)
    root.addHandler(handler)

    # have a separate summary log for high level workflow,
    # in workflows like vmc, we could make use to tail/grep functionality
    # and improve workflow logging on the runner
    # XXX: systest.log will remian same (included DEBUG and above)
    summarylog = 'summary.log'
    summaryhandler = logging.FileHandler(
        os.path.abspath(summarylog), mode='w')
    summaryhandler.addFilter(SummaryLogFilter())
    summaryhandler.setLevel(logging.INFO)
    summaryhandler.setFormatter(formatter)
    summaryhandler.set_name('summary_handler')
    root.addHandler(summaryhandler)
