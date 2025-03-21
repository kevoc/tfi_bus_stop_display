
"""
`bus_stop_display`
====================================================

A graphics class to draw a bus stop display inside a frame buffer

* Author: Kevin O'Connell

"""

try:
    from typing import List, Tuple
except ImportError:
    pass

import time
import micropython

from micropython import const
from .sprites import Hourglass
from .pico_spi_lcd import PiPico_SPI_LCD



# dependant on the font used, char spacing is the minimum that
# should be considered
CHAR_HEIGHT = const(8)
CHAR_WIDTH = const(5)
CHAR_PITCH = const(CHAR_WIDTH + 1)

# The adafruit 5x8 font is actually only 7 pixels high for most
# glyphs. These margins will be used to keep the text in the
# center for most characters.
ROUND_RECT_TEXT_TOP_MARGIN = const(1)
ROUND_RECT_TEXT_BTM_MARGIN = const(ROUND_RECT_TEXT_TOP_MARGIN + 1)
ROUND_RECT_TEXT_VERT_TOTAL_MARGIN = const(ROUND_RECT_TEXT_TOP_MARGIN + ROUND_RECT_TEXT_BTM_MARGIN)
ROUND_RECT_TEXT_HORZ_MARGIN = const(3)

# the horizontal margin from the edge of the display to maintain for all items
GLOBAL_LINE_SPACING = const(2)
GLOBAL_HORZ_MARGIN = const(1)
GLOBAL_LINE_PITCH = const((ROUND_RECT_TEXT_TOP_MARGIN + ROUND_RECT_TEXT_BTM_MARGIN +
                           CHAR_HEIGHT) + GLOBAL_LINE_SPACING)


class BusStopDisplay(PiPico_SPI_LCD):

    def __init__(self):
        PiPico_SPI_LCD.__init__(self)

    def one_px_round_rect(self, x: int, y: int, width: int, height: int,
                          colour: int, opp_colour: int):
        """Draw a rounded rect with a 2-pixel radius."""

        # draw the full un-rounded box
        self.display.fill_rect(x, y, width, height, colour)

        # draw the opposite colours to make the round rects
        self.display.pixel(x, y, opp_colour)
        self.display.pixel(x + width - 1, y, opp_colour)
        self.display.pixel(x, y + height - 1, opp_colour)
        self.display.pixel(x + width - 1, y + height - 1, opp_colour)

    def round_rect_with_text(self, text: str, x: int, y: int, text_colour: int,
                             back_colour: int, min_char_width=None) -> int:
        """Draw a round rect that encompasses the text and then draw
        the text inside the round rect."""

        if min_char_width is not None:
            char_count = max(len(text), min_char_width)
        else:
            char_count = len(text)

        # calculate the y-pixel offset from the y-coordinate required
        # to center the text in the round rect if the specified box is
        # bigger than the number of characters printed
        centre_chars = char_count - len(text)
        x_offset = round(((centre_chars * CHAR_WIDTH) + centre_chars) / 2)

        # draw the background box, with colours inverted since the box is the background
        box_total_width = (char_count * CHAR_WIDTH) + char_count - 1 + (2 * ROUND_RECT_TEXT_HORZ_MARGIN)
        self.one_px_round_rect(x, y, width=box_total_width,
            height=CHAR_HEIGHT + ROUND_RECT_TEXT_VERT_TOTAL_MARGIN,
            colour=back_colour, opp_colour=text_colour)

        # draw the text
        self.text(text, x + ROUND_RECT_TEXT_HORZ_MARGIN + x_offset,
                  y + ROUND_RECT_TEXT_TOP_MARGIN + 1,
                  text_colour)

        return x + box_total_width

    def draw_schedule_line(self, y: int, service_designation: str, service_terminus: str,
                           minutes: str, designation_min_char_width=None):
        """Draw a full line into the frame buffer, including the designation, terminus
         and the minutes until the service arrives. Optionally choose the minimum number
         of characters the designations should be drawn with."""

        # draw the service designation
        x_right = self.round_rect_with_text(service_designation, x=GLOBAL_HORZ_MARGIN, y=y,
                                            text_colour=0, back_colour=1,
                                            min_char_width=designation_min_char_width)

        terminus_x_right = x_right + (ROUND_RECT_TEXT_HORZ_MARGIN + ROUND_RECT_TEXT_TOP_MARGIN)
        terminus_y = y + ROUND_RECT_TEXT_TOP_MARGIN + 1

        minutes_x_left = self.display.width - (CHAR_PITCH * len(minutes)) - GLOBAL_HORZ_MARGIN
        max_chars = ((minutes_x_left - terminus_x_right) // CHAR_PITCH) - 1
        terminus_overflowing = len(service_terminus) > max_chars

        # draw the service terminus name
        self.text(service_terminus[:max_chars], terminus_x_right,
                  terminus_y, 1)

        if terminus_overflowing:
            dot_x_right = terminus_x_right + (max_chars * CHAR_PITCH)
            # if the terminus name is too long, draw two dots to show it should continue
            self.display.pixel(dot_x_right + 1, terminus_y + CHAR_HEIGHT - 2, 1)
            self.display.pixel(dot_x_right + 3, terminus_y + CHAR_HEIGHT - 2, 1)
            self.display.pixel(dot_x_right + 5, terminus_y + CHAR_HEIGHT - 2, 1)

        # draw the minutes until the service departure
        self.text(minutes, self.display.width - (CHAR_PITCH * len(minutes)) - GLOBAL_HORZ_MARGIN,
                  y + ROUND_RECT_TEXT_TOP_MARGIN + 1, 1)

    def draw_schedule_lines(self, y: int, lines: List[Tuple[str, str, str]],
                            designation_min_char_width=None):
        """Draw multiple schedule lines on the display, starting at the y offset."""

        for i, line in enumerate(lines):
            self.draw_schedule_line(y + (i * GLOBAL_LINE_PITCH), *line,
                designation_min_char_width=designation_min_char_width)

    def hourglass_animation(self, x, y, delay=0.2):
        """Show an hourglass waiting animation."""

        self.display.clear_framebuffer()

        for frame in Hourglass.frames:
            self.display.blit(frame, x, y)
            self.display.show()

            time.sleep(delay)

