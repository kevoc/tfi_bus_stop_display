
from machine import SPI, Pin
from micropython import const
from framebuf import MONO_HLSB

from .font import FontRenderer
from .microfont import MicroFont
from .st7920_display import ST7920

# chip select is active high, so set to zero.
CHIP_SELECT = Pin(17, mode=Pin.OUT, value=0)

# lcd reset is active low
LCD_RESET = Pin(16, mode=Pin.OUT, value=1)

# the backlight ground pin is connected via an N-channel MOSFET
# to GP20 for software control of the backlight.
BACKLIGHT = Pin(20, Pin.OUT, Pin.PULL_DOWN)

SPI_BAUD_RATE = const(1_100_000)

DISPLAY_HEIGHT = const(64)
DISPLAY_WIDTH = const(128)

ASSETS = const('/bus_stop_display/assets/')


class PiPico_SPI_LCD:
    """A container class to create the SPI device object."""

    def __init__(self):
        # create a spi object on the
        self.spi_bus = SPI(0, SPI_BAUD_RATE)

        self.display = ST7920(self.spi_bus,
                              width=DISPLAY_WIDTH,
                              height=DISPLAY_HEIGHT,
                              chip_select=CHIP_SELECT,
                              reset=LCD_RESET)

        # TODO: clean up the use of two libraries, should only
        #       need on for rendering both sizes
        fr = FontRenderer(DISPLAY_WIDTH, DISPLAY_HEIGHT,
                          self.display.pixel,
                          font_name=ASSETS + 'font5x8.bin')
        self.standard_text = fr.__enter__()

        # the 15 point font is roughly 10 pixels high.
        # Some characters are 11 pixels though.
        self.large_text = MicroFont(ASSETS + 'victor_R_15.mfnt')

    def clear_framebuffer(self):
        self.display.clear_framebuffer()

    def clear_display(self):
        self.display.clear_display()

    def backlight_on(self):
        BACKLIGHT.value(1)

    def backlight_off(self):
        BACKLIGHT.value(0)

    def text(self, string, x, y, colour):
        """Render standard 8x5 characters."""
        self.standard_text.text(string, x, y, colour)

    def title_text(self, string: str, x: int, y: int, color: int):
        """Render large text, roughly 10 pixels high."""

        # subtracting 2 from the y coordinate because the 15 point font
        # doesn't start at the top of the bounding box. -1 spacing because
        # they are also quite wide!
        self.large_text.write(string, self.display, MONO_HLSB,
                              self.display.width, self.display.height,
                              x, y - 2, color, x_spacing=-1)

    def draw_sprite(self, sprite, x, y, color):
        """Draw a sprite"""

        #self.display.blit

    def show(self):
        self.display.show()
