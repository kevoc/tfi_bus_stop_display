
from micropython import const

from . import log
from . import Controller

SERVICE_DESIGNATION_WIDTH = const(4)


controller = Controller()
controller.init()
controller.start_networking()

log.dump_to_stdout()
print('done')

#
# update_time()
#
# SUBSTITUTE = {
#     'University Hospital': 'CUH'
# }
#
# #
# # for _ in range(4):
# #     bus_stop.hourglass_animation(20, 20)
#
#
# while True:
#     start = time.ticks_us()
#
#     stop_name, stop_times = get_stop_times(231291)
#
#     # apply any name substitutions for headsign
#     for st in stop_times:
#         st['headsign'] = SUBSTITUTE.get(st['headsign'], st['headsign'])
#
#     # only show the next 4 stops
#     if len(stop_times) > 4:
#         stop_times = stop_times[:4]
#
#     bus_stop.clear_framebuffer()
#     bus_stop.title_text(stop_name, 0, 0, color=1)
#     bus_stop.draw_clock(91, 1, now_epoch())
#
#     bus_stop.draw_schedule_lines(y=14,
#         lines=[(t['route'], t['headsign'], str(t['minutes']))
#                 for t in stop_times],
#         designation_min_char_width=SERVICE_DESIGNATION_WIDTH)
#
#     bus_stop.show()
#
#     print(f'update duration: {(time.ticks_us() - start) / 1000:.1f} ms.')
#     time.sleep(5)
#
#
# bus_stop.clear_display()
# bus_stop.backlight_off()
