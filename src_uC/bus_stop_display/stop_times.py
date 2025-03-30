
import gc
import time
import ujson as json
import urequests as requests


from . import log
from . import ConfigImportMixin

from .time_tools import now_epoch, timestamp_to_epoch


# pre-allocate a response buffer for the data, so there's always enough
# memory for the response.
_RESPONSE_BUFFER = bytearray(4096)


def get_stop_times(stop_id, url):
    """Request the latest stop times for the given stop_id."""

    # we must garbage collect before attempting a web request to make sure
    # there's enough memory to parse all of the data.
    gc.collect()

    r = requests.get(url.format(stop_id),
                     headers={'Accept': 'application/json'})
    byte_count = r.raw.readinto(_RESPONSE_BUFFER)
    all_stops = json.loads(_RESPONSE_BUFFER[:byte_count])

    stop_str = str(stop_id)
    if stop_str not in all_stops:
        return None
    else:
        stop_data = all_stops[stop_str]
        return stop_data['stop_name'], stop_data['arrivals']


def _is_valid_arrival(arr: dict):
    """Return true if the given arrival dict has both a headsign
    and an estimated arrival."""

    return (arr['real_time_arrival'] not in [None, ''] and
            arr['headsign'] not in [None, ''])


def prepare_service_arrivals(arrivals, name_subs):
    """This function filters the provided data from the backend,
    removing known erroneous data from the source."""

    # the GTFS backend provides all times in UTC
    now = now_epoch(apply_dst_offset=False)

    prepped = []
    for arr in filter(_is_valid_arrival, arrivals):
        arr_epoch = timestamp_to_epoch(arr['real_time_arrival'])
        is_scheduled = arr['real_time_arrival'] == arr['scheduled_arrival']

        secs = arr_epoch - now
        headsign = name_subs.get(arr['headsign'], arr['headsign'])

        prepped.append({'route': arr['route'],
                        'headsign': headsign,
                        'scheduled': is_scheduled,
                        'minutes': secs // 60,
                        'seconds': secs})

    return prepped


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


class BusStop:
    """Parse a full line from the settings file."""

    def __init__(self, line, backend_url):
        self._stop_ids = []
        self._name = None
        self._is_default = False
        self._backend_url = backend_url
        self._arrival_cache = {}
        self._name_subs = None
        self._last_good_update = 0

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

        log.info(f'Loaded stop: {stop_ids}')

    def set_name_substitutions(self, sub_dict):
        """Set the name substitution dict for destinations."""
        self._name_subs = sub_dict

    def update_times(self):
        """Update the cache of arrivals for this stop."""

        for stop_id in self._stop_ids:
            stop_name, arrivals = get_stop_times(stop_id, self._backend_url)
            self._name = self._name or stop_name

            if arrivals or (time.time() - self._last_good_update) > 90:
                # during GTFS static data updates, the backend deletes the entire
                # cache, and rebuilds from scratch. Takes about 60 seconds.
                # If you update during a cache refresh, you'll get no arrivals.
                # This if statement will update only if there's valid data, or
                # if it's been 90 seconds without an update. This is to stop the
                # last service of the night from getting stuck on the screen.
                self._arrival_cache[stop_id] = arrivals
                self._last_good_update = time.time()

    @property
    def name(self):
        return self._name

    @property
    def all_arrivals(self):
        return [a for stop_id, arrivals in self._arrival_cache.items()
                  for a in arrivals]

    def arrival_board(self, count=4):
        """Return the next `count` services for the arrival board of this stop."""

        prepped = prepare_service_arrivals(self.all_arrivals, self._name_subs)
        return list(sorted(prepped, key=lambda x: x['seconds']))[:count]


class BusStopContainer(ConfigImportMixin):
    """A container for the general settings of the display."""

    def __init__(self, path, backend_url):
        ConfigImportMixin.__init__(self)
        self.import_list_settings(path)

        self._stops = []
        self._url = backend_url
        self._build_stops()

    def __getitem__(self, item) -> BusStop:
        return self._stops[item]

    def _build_stops(self):
        """Create stop objects for all stops"""

        for line in self.config:
            try:
                stop_obj = BusStop(line, self._url)
            except Exception as exc:
                log.error(f'error parsing line: {line}')
                log.error(f'   -> {exc}')
                raise

            self._stops.append(stop_obj)

    def set_name_substitutions(self, sub_dict):
        for stop in self._stops:
            stop.set_name_substitutions(sub_dict)

    @property
    def stop_count(self):
        return len(self._stops)

    def update_times(self):
        """Update the cache of all bus stop times."""

        for stop in self._stops:
            stop.update_times()
