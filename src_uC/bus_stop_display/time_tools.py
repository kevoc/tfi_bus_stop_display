
import time
import ntptime

from . import log


# NOTE: on the rp2 port, the last 2 integers in the tuple to mktime()
#       can be 0 without affecting the calculated date. These are
#       the "day-of-week" and "day-of-year" values respectively.
#
# UTC offset for daylight savings time.
# This should be an hour amount that's applied to UTC time to correct
# it. The key of the dict is a date, after which that offset is applied.
UTC_OFFSET = {
    time.mktime((2024, 10, 27, 2, 0, 0, 0, 0)): 0,
    time.mktime((2025, 3, 30, 1, 0, 0, 0, 0)): 1,
    time.mktime((2025, 10, 26, 2, 0, 0, 0, 0)): 0,
    time.mktime((2026, 3, 29, 1, 0, 0, 0, 0)): 1,
    time.mktime((2026, 10, 25, 2, 0, 0, 0, 0)): 0,
    time.mktime((2027, 3, 28, 1, 0, 0, 0, 0)): 1,
    time.mktime((2027, 10, 31, 2, 0, 0, 0, 0)): 0,
    time.mktime((2028, 3, 26, 1, 0, 0, 0, 0)): 1,
    time.mktime((2028, 10, 29, 2, 0, 0, 0, 0)): 0,
    time.mktime((2029, 3, 25, 1, 0, 0, 0, 0)): 1,
    time.mktime((2029, 10, 28, 2, 0, 0, 0, 0)): 0,
    time.mktime((2030, 3, 31, 1, 0, 0, 0, 0)): 1,
    time.mktime((2030, 10, 27, 2, 0, 0, 0, 0)): 0,
}

_WEEKDAY = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

def now():
    """Return the current time as a string."""
    year, month, day, hours, minutes, seconds, weekday, day_of_year = time.localtime()
    return f'{year}-{month:02d}-{day:02d} {hours:02d}:{minutes:02d}:{seconds:02d}'


def update_time(time_servers):
    """Contact the NTP time servers to get the current time."""

    # loop through all servers until one of them gives a valid time
    for server in time_servers:
        try:
            ntptime.host = server
            ntptime.settime()
        except Exception as exc:
            log.error(f'an exception was thrown while updating time from: {server}')
            log.error(f'    -> Exception {exc}')
        else:
            log.info(f'Successfully updated time from {server}')
            return True

    return False


def _utc_offset_hours(epoch):
    """Return the number of UTC hours offset to be applied
    for Daylight Savings Time."""

    # find the appropriate DST offset
    dates = list(sorted(UTC_OFFSET.keys()))
    for i in range(len(dates)):
        if dates[i] <= epoch < dates[i+1]:
            return UTC_OFFSET[dates[i]]

    # No DST offsets will be applied after Oct 2030 without
    # a firmware update
    return 0


# note: the data backend provides times in UTC, not corrected
#       for daylight savings time. The on-display clock needs
#       to be corrected for UTC though.
def now_epoch(apply_dst_offset=True):
    """Get the current time in seconds, i.e. UTC plus any
    daylight savings time offset."""

    cur_time = time.time()

    if not apply_dst_offset:
        return cur_time

    return time.time() + 3600 * _utc_offset_hours(cur_time)


def timestamp_to_epoch(timestamp):
    """Convert a string timestamp to epoch time.
    Format as per data backend: 2025-03-21T18:34:10
    """

    date_part, time_part = timestamp.split('T')

    try:
        epoch = time.mktime(tuple(int(x) for x in
                    tuple(date_part.split('-') + time_part.split(':')) + (0, 0)))
    except Exception as exc:
        raise ValueError(f'bad timestamp: {timestamp} -> {exc}')
    else:
        return epoch
