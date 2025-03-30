
import time
from micropython import const

from . import log
from . import Controller


controller = Controller()
controller.init()
controller.start_networking()
controller.import_other_configs()


while True:
    controller.update_arrival_time_cache()
    controller.draw_arrivals_board(0)
    time.sleep(5)

