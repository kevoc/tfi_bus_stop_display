
import time
import ntptime

from .wifi import WifiController
from .log_tools import open_logfile
from .config import import_list_settings


_TIME_SERVERS = const('/settings/time_servers.txt')


def connect():
    wlan = WifiController()
    wlan.network_scan()
    wlan.connect()

