
import time
from micropython import const
from bus_stop_display import BusStopDisplay


SERVICE_DESIGNATION_WIDTH = const(4)


bus_stop = BusStopDisplay()

for offset in range(30):
    start = time.monotonic()

    bus_stop.clear_framebuffer()
    bus_stop.draw_schedule_lines(y=14,
        lines=[('123', 'Cork',               str(2 + offset)),
               ('X1',  'Limerick1234567890', str(8 + offset)),
               ('456', 'Dublin',             str(14 + offset)),
               ('XYZ', 'Belfast 67890',      str(50 + offset))],
        designation_min_char_width=SERVICE_DESIGNATION_WIDTH)

    bus_stop.show()

    print(f'update duration: {time.monotonic() - start:.3f}')
