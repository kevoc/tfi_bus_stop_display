
"""
`log_tools`
====================================================

A set of logging tools to make it easy to log things
and automatically rotate log files.

* Author: Kevin O'Connell

"""

import os
import time
from micropython import const

# where on the file system to store logs
_LOG_FOLDER = const('/logs')

# when rotating files, how many older files to keep.
_BACKUP_COUNT = const(5)

_FORMAT = const('{time:9.3f} {level:<8s} {msg}')


# make the log folder, ignore the error if it already exists.
try:
    os.mkdir(_LOG_FOLDER)
except OSError:
    pass


def _file_exists(path):
    """Return True if a path exists, False otherwise."""

    try:
        os.stat(path)
        return True
    except OSError:
        return False


def rotate_file(filename):
    """Rotate the given filename."""

    # this code was taken from the cpython
    # logging.handlers.RotatingFileHandler() doRollover method
    # with minor adaptions to work with micropython

    if _BACKUP_COUNT > 0 and _file_exists(_LOG_FOLDER + '/' + filename):
        for i in range(_BACKUP_COUNT - 1, 0, -1):
            sfn = _LOG_FOLDER + f'/{filename}.{i}'
            dfn = _LOG_FOLDER + f'/{filename}.{i + 1}'

            if _file_exists(sfn):
                if _file_exists(dfn):
                    os.remove(dfn)
                os.rename(sfn, dfn)
        dfn = _LOG_FOLDER + f'/{filename}.1'
        if _file_exists(dfn):
            os.remove(dfn)
        os.rename(_LOG_FOLDER + '/' + filename, dfn)


def open_logfile(filename, mode, rotate=True):
    """Rotate any logfiles currently on the flash, and
    return a file handle for a new file"""

    if _file_exists(_LOG_FOLDER + '/' + filename) \
            and rotate and 'a' not in mode:
        rotate_file(filename)

    return open(_LOG_FOLDER + '/' + filename, mode)


# CAVEAT:
#   When using this mixin, log messages get stored in memory
#   until they are manually dumped to the flash. This is to
#   minimise flash writes for speed and reduced wear of the
#   flash cells. The main use case for this is during startup
#   and parsing of config files. The parsing and dump of
#   logs happens in relative short order. Use the convenience
#   decorator @dump_on_completion to dump logs to flash after
#   a function is done executing.
class LoggingMixin:
    """A logger mixin that can be used for debug logging in classes."""

    def __init__(self, log_file):
        self._msgs = []
        self.log_file = log_file

        # rotate the file once at the very beginning
        rotate_file(log_file)

    def log(self, level, message):
        self._msgs.append(_FORMAT.format(time=1.0e-3 * time.ticks_ms(),
                                         level=level,
                                         msg=message))

    def log_info(self, message):
        self.log('INFO', message)

    def log_error(self, message):
        self.log('ERROR', message)

    def dump(self):
        if self._msgs:
            with open_logfile(self.log_file, mode='a', rotate=False) as f:
                for msg in self._msgs:
                    f.write(msg)
                    f.write('\n')
            self._msgs = []


def dump_on_completion(func):
    """Call the dump method of the class after the decorated method
    has completed execution."""

    def _wrapper(self, *args, **kwargs):
        try:
            result = func(self, *args, **kwargs)
        finally:
            self.dump()
        return result

    return _wrapper
