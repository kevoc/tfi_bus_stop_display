
import gc
import time
from micropython import const
from display import BusStopDisplay, sprites


def mem_usage():
    """Force a garbage collection, and dump to the total
    free/allocated memory."""
    gc.collect()
    free, alloc = gc.mem_free(), gc.mem_alloc()
    total = free + alloc
    print(f'{free:,d} free of {total:,d} bytes ({free/total:.2%})')


SERVICE_DESIGNATION_WIDTH = const(4)


bus_stop = BusStopDisplay()
bus_stop.backlight_on()

for _ in range(4):
    bus_stop.hourglass_animation(20, 20)


for offset in range(30):
    start = time.ticks_us()

    bus_stop.clear_framebuffer()
    bus_stop.title_text('Patrick St.', 0, 0, color=1)
    bus_stop.draw_schedule_lines(y=14,
        lines=[('123', 'Cork',     str(2 + offset)),
               ('X1',  'Limerick', str(8 + offset)),
               ('456', 'Dublin',   str(14 + offset)),
               ('XYZ', 'Belfast',  str(50 + offset))],
        designation_min_char_width=SERVICE_DESIGNATION_WIDTH)

    bus_stop.show()

    print(f'update duration: {(time.ticks_us() - start) / 1000:.1f} ms.')

mem_usage()

bus_stop.clear_display()
bus_stop.backlight_off()
