
import time
import ntptime

from . import log
from . import WifiController
from . import BusStopDisplay

from . import GeneralConfig
from . import StopsConfig

from . import update_time
from . import MQTTController


_GENERAL_CONFIG = const('/settings/general.cfg')
_STOPS_CONFIG = const('/settings/stops.cfg')
_NAME_SUBS_CONFIG = const('/settings/name_subs.cfg')


# an error decorator to display an error on the
# LCD any time a critical error happens.
def show_error(error_name):
    def _decorator(function):
        def _wrapper(self, *args, **kwargs):
            try:
                return function(self, *args, **kwargs)
            except Exception as exc:
                log.error(f'{exc}')
                log.dump()
                self.show_error(error_name)
        return _wrapper
    return _decorator


class Controller:
    """Main controller for the power up sequence."""

    def __init__(self):
        self._display = BusStopDisplay()
        self._general_cfg = None
        self._mqtt = None
        self._wlan = None

    def init(self):
        """Run all the initialisation steps that only needs to
        be done once."""

        self._display.backlight_on()
        self.import_general_config()

    def start_networking(self):
        """Run all the networking setup commands."""
        self.connect_wifi()
        self.update_time()
        self.connect_to_mqtt()

        if self._mqtt is not None:
            log.add_mqtt(self._mqtt, '/log')
        else:
            log.dump_to_flash()
            log.discard_all_future_log_messages()

    #@show_error('importing settings: general.cfg')
    def import_general_config(self):
        """Import the general config settings."""
        self._general_cfg = GeneralConfig(_GENERAL_CONFIG)

    #@show_error('connecting to wifi')
    def connect_wifi(self):
        self._wlan = WifiController(self._general_cfg['wifi_network'],
                                    self._general_cfg['wifi_password'],
                                    self._general_cfg['wifi_connect_timeout'])
        self._wlan.connect()

    #@show_error('getting the time')
    def update_time(self):
        update_time(self._general_cfg['time_servers'])

    #@show_error('connecting to mqtt')
    def connect_to_mqtt(self):
        if self._general_cfg['use_mqtt']:
            try:
                mqtt = MQTTController.over_ssl(
                    mqtt_server=self._general_cfg['mqtt_server'],
                    auth_cert_file=self._general_cfg['mqtt_auth_cert']
                )
            except Exception as exc:
                log.error('Unable to connect to MQTT')
                log.error(f'   -> {exc}')
                self._mqtt = None
            else:
                self._mqtt = mqtt
                self._mqtt.set_root_topic(self._general_cfg['mqtt_root_topic'])
