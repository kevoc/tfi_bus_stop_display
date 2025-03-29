
"""
`config`
====================================================

A config file import class with abstractions for all
all settings to be imported from the settings folder.

* Author: Kevin O'Connell

"""

import os


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


class ConfigImportMixin:
    """A mixin to assist in importing settings from a config file."""

    def __init__(self):
        self.config = None

        self._imported_file = None

        # this is used as a temporary staging variable for the imported
        # config file as it's being parsed and validated.
        self._staging_config = {}

    def import_key_value_settings(self, path):
        """Import the wifi config file."""

        self.config = {}
        self._imported_file = path

        try:
            self._staging_config = import_key_value_settings(path)
        except Exception as exc:
            self.log_error(f'bad settings file: {path}')
            self.log_error(f'   -> {exc}')
            raise

    def import_required_param(self, name, ptype=None):
        """Import the required parameter given by name"""

        if name not in self._staging_config:
            self.log_error(f'"{name}" is a required setting in {self._imported_file}')
            raise ValueError(f'{name} not specified in settings')
        else:
            if ptype is None:
                value = self._staging_config[name]
            else:
                try:
                    value = ptype(self._staging_config[name])
                except TypeError:
                    self.log_error(f'setting "{name}" from "{self._imported_file}" ' + \
                                   f'could not be coerced to {ptype}: {self._staging_config[name]}')
                    raise TypeError(f'bad "{name}" type')

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
                self.log_error(f'setting "{name}" from "{self._imported_file}" ' + \
                               f'could not be coerced to {ptype}: {self._staging_config[name]}')
                raise TypeError(f'bad "{name}" type')

            self.config[name] = value
