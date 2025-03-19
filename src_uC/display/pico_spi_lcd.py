

from .st7920_display import ST7920

from micropython import const
from machine import SPI, Pin


# chip select is active high, so set to zero.
CHIP_SELECT = Pin(17, mode=Pin.OUT, value=0)

# lcd reset is active low
LCD_RESET = Pin(16, mode=Pin.OUT, value=1)

SPI_BAUD_RATE = const(1_100_000)

DISPLAY_HEIGHT = const(64)
DISPLAY_WIDTH = const(128)


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

    def clear_framebuffer(self):
        self.display.clear_framebuffer()

    def clear_display(self):
        self.display.clear_display()

    def show(self):
        self.display.show()
