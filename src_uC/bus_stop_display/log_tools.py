
"""
`log_tools`
====================================================

A set of logging tools to make it easy to log things
and automatically rotate log files.

* Author: Kevin O'Connell

"""

import os
import sys
import time
from uio import StringIO
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


def log_traceback(exc):
    """Dump the full stack trace to the log."""

    from . import log

    str_buff = StringIO()
    sys.print_exception(exc, str_buff)

    for line in str_buff.getvalue().splitlines():
        log.error(f'  {line}')


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
#   When using this logger, log messages get stored in memory
#   until they are either manually dumped to the flash, or
#   uploaded to a log server over MQTT.
class Logger:
    """A logger for logging errors and info messages."""

    def __init__(self, log_file):
        self._msgs = []
        self.log_file = log_file

        self._mqtt = None
        self._mqtt_topic = None

        self._disabled = False

        # rotate the file once at the very beginning
        rotate_file(log_file)

    def add_mqtt(self, server, topic, dump=True):
        """Add an MQTT server to consume the logs."""

        self._mqtt = server
        self._mqtt_topic = topic

        if dump:
            self.dump_to_mqtt()

    def log(self, level, message):
        if self._disabled:
            return

        self._msgs.append(_FORMAT.format(time=1.0e-3 * time.ticks_ms(),
                                         level=level,
                                         msg=message))

    def info(self, message):
        self.log('INFO', message)

    def error(self, message):
        self.log('ERROR', message)

    def dump_to_stdout(self):
        if self._msgs:
            for msg in self._msgs:
                print(msg)
            self._msgs = []

    def dump_to_flash(self):
        if self._msgs:
            with open_logfile(self.log_file, mode='a', rotate=False) as f:
                for msg in self._msgs:
                    f.write(msg)
                    f.write('\n')
            self._msgs = []

    def dump_to_mqtt(self):
        if self._msgs:
            for msg in self._msgs:
                self._mqtt.publish(self._mqtt_topic, msg)
            self._msgs = []

    def dump(self, force=False):
        """Dump to MQTT if configured, otherwise wait until
        MQTT is configured. `force` should be used when an exception
        is thrown, so the log gets persisted to flash. It can be
        captured at a later stage if network is unavailable."""

        if self._mqtt is not None:
            try:
                self.dump_to_mqtt()
            except Exception as exc:
                self.error('Unable to persist logs to MQTT, dumping to flash')
                log_traceback(exc)

                self.dump_to_flash()

        elif force:
            self.dump_to_flash()

    def discard_all_future_log_messages(self):
        """Used after the boot up sequence is complete, all
        log messages will be written to flash for later analysis,
        and any future log messages will be discarded."""

        self.dump_to_flash()
        self._disabled = True
