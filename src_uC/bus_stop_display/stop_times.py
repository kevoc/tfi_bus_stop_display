
import gc
import ujson as json
import urequests as requests

from micropython import const

from .time_manager import now_epoch, timestamp_to_epoch


# pre-allocate a response buffer for the data, so there's always enough
# memory for the response.
_RESPONSE_BUFFER = bytearray(4096)


def get_stop_times(stop_id):
    """Request the latest stop times for the given stop_id."""

    # we must garbage collect before attempting a web request to make sure
    # there's enough memory to parse all of the data.
    gc.collect()

    r = requests.get(_BACKEND_URL.format(stop_id),
                     headers={'Accept': 'application/json'})
    byte_count = r.raw.readinto(_RESPONSE_BUFFER)
    all_stops = json.loads(_RESPONSE_BUFFER[:byte_count])

    stop_str = str(stop_id)
    if stop_str not in all_stops:
        return None
    else:
        stop_data = all_stops[stop_str]
        return (stop_data['stop_name'],
                prepare_service_arrivals(stop_data['arrivals']))


def _is_valid_arrival(arr: dict):
    """Return true if the given arrival dict has both a headsign
    and an estimated arrival."""

    return (arr['real_time_arrival'] not in [None, ''] and
            arr['headsign'] not in [None, ''])


##################################################################
### This is the function that converts the raw data from the
### server into a filtered list of services and minutes until
### the service arrives.
##################################################################
def prepare_service_arrivals(arrivals):
    """This function filters the provided data from the backend,
    removing known erroneous data from the source."""

    now = now_epoch()

    prepped = []
    for arr in filter(_is_valid_arrival, arrivals):
        arr_epoch = timestamp_to_epoch(arr['real_time_arrival'])
        is_scheduled = arr['real_time_arrival'] == arr['scheduled_arrival']

        prepped.append({'route': arr['route'],
                        'headsign': arr['headsign'],
                        'scheduled': is_scheduled,
                        'minutes': (arr_epoch - now) // 60})

    return prepped