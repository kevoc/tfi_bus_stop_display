
import time
import ntptime

from . import log
from . import log_traceback
from . import WifiController
from . import BusStopDisplay
from . import BusStopContainer

from . import now_epoch

from . import GeneralConfig
from . import import_key_value_settings

from . import update_time
from . import MQTTController


_GENERAL_CONFIG = const('/settings/general.cfg')
_STOPS_CONFIG = const('/settings/stops.cfg')
_NAME_SUBS_CONFIG = const('/settings/name_subs.cfg')


_SERVICE_DESIGNATION_WIDTH = const(4)


# an error decorator to display an error on the
# LCD any time a critical error happens.
def show_error(error_name):
    def _decorator(function):
        def _wrapper(*args, **kwargs):
            try:
                return function(*args, **kwargs)
            except Exception as exc:
                log.error(f'Exception thrown while {error_name}:')
                log_traceback(exc)

                # TODO: implement error message on screen
                # self.show_error(error_name)
                log.dump(force=True)
                raise
            finally:
                log.dump()

        return _wrapper
    return _decorator


class Controller:
    """Main controller for the power up sequence."""

    def __init__(self):
        self._display = BusStopDisplay()
        self._mqtt = None
        self._wlan = None

        self._general_cfg: GeneralConfig = None
        self._stops: BusStopContainer = None
        self._name_subs: dict = None

    def init(self):
        """Run all the initialisation steps that only needs to
        be done once."""

        log.info('Starting up...')
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

    @show_error('importing: general.cfg')
    def import_general_config(self):
        """Import the general config settings."""
        self._general_cfg = GeneralConfig(_GENERAL_CONFIG)

    def import_other_configs(self):
        """Import the stops and name subs config."""
        self._import_stops_config()
        self._import_name_subs_config()
        self._stops.set_name_substitutions(self._name_subs)

    @show_error('importing: stops.cfg')
    def _import_stops_config(self):
        """Import the general config settings."""
        self._stops = BusStopContainer(_STOPS_CONFIG,
                                       self._general_cfg['data_backend_url'])
        log.info(f'Imported {self._stops.stop_count} bus stop(s) from "stops.cfg"')

    @show_error('importing: name_subs.cfg')
    def _import_name_subs_config(self):
        """Import the general config settings."""
        self._name_subs = import_key_value_settings(_NAME_SUBS_CONFIG)
        log.info(f'Imported {len(self._name_subs)} substitution(s) from "name_subs.cfg"')

    @show_error('connecting to wifi')
    def connect_wifi(self):
        self._wlan = WifiController(self._general_cfg['wifi_network'],
                                    self._general_cfg['wifi_password'],
                                    self._general_cfg['wifi_connect_timeout'])
        self._wlan.connect()

    @show_error('getting the time')
    def update_time(self):
        update_time(self._general_cfg['time_servers'])

    @show_error('connecting to mqtt')
    def connect_to_mqtt(self):
        if self._general_cfg['use_mqtt']:
            try:
                mqtt = MQTTController.over_ssl(
                    mqtt_server=self._general_cfg['mqtt_server'],
                    auth_cert_file=self._general_cfg['mqtt_auth_cert']
                )
            except Exception as exc:
                log.error('Unable to connect to MQTT')
                log_traceback(exc)
                self._mqtt = None
            else:
                self._mqtt = mqtt
                self._mqtt.set_root_topic(self._general_cfg['mqtt_root_topic'])

    @show_error('updating arrival times')
    def update_arrival_time_cache(self):
        """Update all time for all monitored bus stops"""
        self._stops.update_times()
        log.info('finished updating arrivals for all bus stops')

    @show_error('drawing arrivals board')
    def draw_arrivals_board(self, stop_index):
        """Draw the given arrival board index."""

        start = time.ticks_us()

        bus_stop = self._stops[stop_index]

        self._display.clear_framebuffer()
        self._display.title_text(bus_stop.name, 0, 0, color=1)
        self._display.draw_clock(91, 1, now_epoch())

        arrivals_board = [(t['route'], t['headsign'], str(t['minutes']))
                                for t in bus_stop.arrival_board()]

        self._display.draw_schedule_lines(y=14, lines=arrivals_board,
                                          designation_min_char_width=_SERVICE_DESIGNATION_WIDTH)

        self._display.show()

        log.info(f'display update took {(time.ticks_us() - start) / 1000:.1f} ms.')
