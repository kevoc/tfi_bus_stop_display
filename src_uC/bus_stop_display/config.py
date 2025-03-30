
"""
`config`
====================================================

A config file import class with abstractions for all
all settings to be imported from the settings folder.

* Author: Kevin O'Connell

"""

import os
from . import log


def import_key_value_settings(path):
    """Import the given settings file, expecting key-value pairs.
    The seperator for keys/values will be the first = in a line.
    All leading white space will be stripped from the file, allowing
    indentation for clearer layout.
    Any line starting with # will be ignored.
    Empty lines will be ignored.
    All keys must be unique, if there are collisions, the last will
    be stored."""

    dictionary = {}
    with open(path, 'r') as f:
        for i, line in enumerate(f.readlines()):
            line = line.lstrip()
            if not line or line.startswith('#'):
                continue
            if '=' not in line:  # this is invalid
                filename = os.path.basename(path)
                raise ValueError(f'{filename}: no equals in line {i + 1}')

            key, value = line.split('=', 1)

            # strip any new line characters from the value, and store!
            dictionary[key] = value.rstrip('\r\n')

    return dictionary


def import_list_settings(path):
    """Import the given settings file, expecting a list of strings.
    All leading/trailing white space will be stripped from each line
    Any line starting with # will be ignored. Empty lines will be
    ignored."""

    lines = []
    with open(path, 'r') as f:
        for i, line in enumerate(f.readlines()):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            lines.append(line)
    return lines


def boolean(value_str):
    """Convert a string yes/no to a boolean"""

    value_str = value_str.lower()
    if value_str == 'yes':
        return True
    elif value_str == 'no':
        return False
    else:
        raise ValueError('only "yes" or "no" are valid boolean literals')


class ConfigImportMixin:
    """A mixin to assist in importing settings from a config file."""

    def __init__(self):
        self.config = None

        self._imported_file = None

        # this is used as a temporary staging variable for the imported
        # config file as it's being parsed and validated.
        self._staging_config = None

    def __getitem__(self, item):
        return self.config[item]

    def import_key_value_settings(self, path):
        """Import the current config file as key/value pairs."""

        self.config = {}
        self._imported_file = path

        try:
            self._staging_config = import_key_value_settings(path)
        except Exception as exc:
            log.error(f'bad settings file: {path}')
            log.error(f'   -> {exc}')
            raise

    def import_list_settings(self, path):
        """Import the current config file as a list of strings."""

        self.config = []
        self._imported_file = path

        try:
            self.config = import_list_settings(path)
        except Exception as exc:
            log.error(f'bad settings file: {path}')
            log.error(f'   -> {exc}')
            raise

    def import_required_param(self, name, ptype=None):
        """Import the required parameter given by name"""

        if name not in self._staging_config:
            log.error(f'"{name}" is a required setting in {self._imported_file}')
            raise ValueError(f'{name} not specified in settings')
        else:
            if ptype is None:
                value = self._staging_config[name]
            else:
                try:
                    value = ptype(self._staging_config[name])
                except TypeError:
                    log.error(f'setting "{name}" from "{self._imported_file}" ' + \
                              f'could not be coerced to {ptype}: {self._staging_config[name]}')
                    raise TypeError(f'bad "{name}" type')
                except ValueError:
                    log.error(f'value of setting "{name}" from "{self._imported_file}" ' + \
                              f'was not recognised: {self._staging_config[name]}')
                    raise

            self.config[name] = value

    def import_optional_param(self, name, default):
        """Import the optional parameter given by name, type casting to
        be the same type as the default value."""

        if name not in self._staging_config:
            self.config[name] = default
        else:
            ptype = type(default)
            try:
                value = ptype(self._staging_config[name])
            except TypeError:
                log.error(f'setting "{name}" from "{self._imported_file}" ' + \
                          f'could not be coerced to {ptype}: {self._staging_config[name]}')
                raise TypeError(f'bad "{name}" type')

            self.config[name] = value


class GeneralConfig(ConfigImportMixin):
    """A container for the general settings of the display."""

    def __init__(self, path):
        ConfigImportMixin.__init__(self)
        self.import_key_value_settings(path)
        self.import_required_param('wifi_network', ptype=str)
        self.import_required_param('wifi_password', ptype=str)

        self.import_optional_param('wifi_connect_timeout', default=10)
        self.import_optional_param('wifi_connect_retries', default=5)
        self.import_optional_param('wifi_connect_cooldown', default=10)

        self.import_required_param('data_backend_url', ptype=str)
        self.import_required_param('time_servers', ptype=str)
        self.config['time_servers'] = self.config['time_servers'].split(',')

        self.import_required_param('use_mqtt', ptype=boolean)

        if self['use_mqtt']:
            self.import_required_param('mqtt_server')
            self.import_optional_param('mqtt_username', default='')
            self.import_optional_param('mqtt_password', default='')
            self.import_optional_param('mqtt_auth_cert', default='')
            self.import_required_param('mqtt_root_topic')


def is_integer(my_str):
    """Return true if the given string is only numbers."""
    # 48 = ascii 0, 57 = ascii 9
    return all([48 <= ord(c) <= 57 for c in my_str])


def split_stops_and_prefs(pieces):
    """Given a list of stop ids with optional prefs,
    split them into two lists. All stop IDs must come
    at the beginning of the list."""

    stop_ids, prefs = [], []
    for i, piece in enumerate(pieces):
        if is_integer(piece):
            stop_ids.append(piece)
        else:
            # the first non-integer value is the end of the
            # list of stop ids.
            prefs.extend(pieces[i + 1:])
            break
    return stop_ids, prefs


class Stop:
    """Parse a full line from the settings file."""

    def __init__(self, line):
        self._stop_ids = []
        self._name = None
        self._is_default = False

        self.parse(line)

    def parse(self, line: str):
        pieces = [p.strip() for p in line.split(',')]
        stop_ids, prefs = split_stops_and_prefs(pieces)

        try:
            stop_ids = [int(stop) for stop in stop_ids]
        except Exception as exc:
            raise ValueError(f'stop IDs could not be coerced to integers: {exc}')
        else:
            self._stop_ids = stop_ids

        if len(self._stop_ids) == 0:
            raise ValueError('no stop IDs were found')

        for preference in prefs:
            if preference.lower() == 'default':
                self._is_default = True
            elif preference.lower().startswith('name='):
                self._name = preference.split('=')[1]
            else:
                raise ValueError(f'invalid preference: {preference}')


class StopsConfig(ConfigImportMixin):
    """A container for the general settings of the display."""

    def __init__(self, path):
        ConfigImportMixin.__init__(self)
        self.import_list_settings(path)

        self._stops = []
        self._build_stops()

    def _build_stops(self):
        """Create stop objects for all stops"""

        for line in self.config:
            try:
                stop_obj = Stop(line)
            except Exception as exc:
                log.error(f'error parsing line: {line}')
                log.error(f'   -> {exc}')
                raise

