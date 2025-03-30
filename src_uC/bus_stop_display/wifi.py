
"""
`wifi`
====================================================

Wifi connection and network scans.

* Author: Kevin O'Connell

"""


import time
import json
import network
from micropython import const

from . import log


SECURITY = {
    0: 'open',
    1: 'WEP',
    2: 'WPA-PSK',
    3: 'WPA2-PSK',
    4: 'WPA/WPA2-PSK',
}


class WifiController:
    """A wifi controller to connect to and manage wifi."""

    def __init__(self, network_name: str, password: str,
                 connect_timeout: int = 10):

        self._network = network_name
        self._password = password
        self._connect_timeout = connect_timeout

        self.wlan = network.WLAN(network.WLAN.IF_STA)
        self.wlan.active(True)

    def network_scan(self):
        """Run a network scan, logging the results."""

        start = time.ticks_ms()

        for network in self.wlan.scan():
            ssid, bssid, channel, RSSI, security, hidden = network

            bssid_str = ":".join([f"{b:02X}" for b in bssid])

            log.info(json.dumps(
                {'SSID': ssid, 'BSSID': bssid_str, 'Channel': channel,
                 'RSSI': RSSI, 'Security': SECURITY.get(security, security),
                 'Hidden': hidden}))

        log.info(f'Scan took {1.0e-3 * (time.ticks_ms() - start):.2f} secs.')

    def connect(self):
        """Connect to the network loaded from the config file."""

        log.info(f'Connecting to network "{self._network}" with timeout of {self._connect_timeout} secs.')
        self.wlan.connect(self._network, self._password)

        start = time.ticks_ms()
        while (time.ticks_ms() - start) < (1000 * self._connect_timeout):
            if self.wlan_status != 'connecting':
                break

            time.sleep_ms(100)

        status = self.wlan_status
        if status == 'connecting':
            log.error(f'timeout waiting for network connection')
            raise RuntimeError('timeout while connecting')
        elif self.wlan_status != 'got IP':
            raise RuntimeError(self.wlan_status)
        elif not self.wlan.isconnected():
            raise RuntimeError('unspecified error occurred')

        log.info(f'successful connection after {1.0e-3 * (time.ticks_ms() - start):.2f} secs.')

        self.log_ip_address()

    @property
    def wlan_status(self):
        """Return a string description of the status"""

        status = self.wlan.status()

        if status == network.STAT_IDLE:
            return 'idle'
        elif status == network.STAT_CONNECTING:
            return 'connecting'
        elif status == network.STAT_NO_AP_FOUND:
            return 'access point not found'
        elif status == network.STAT_WRONG_PASSWORD:
            return 'wrong password'
        elif status == network.STAT_CONNECT_FAIL:
            return 'connection failed'
        elif status == network.STAT_GOT_IP:
            return 'got IP'
        else:
            return f'unrecognised status: {status}'

    def log_ip_address(self):
        """Dump the IP address information to the log."""

        ip, subnet, gateway, dns = self.wlan.ifconfig()

        log.info(json.dumps({'ip': ip, 'subnet': subnet,
                             'gateway': gateway, 'dns': dns}))
