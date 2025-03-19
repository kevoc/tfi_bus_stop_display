
#


import board
import busio
import digitalio

from micropython import const
from st7920_display import ST7920
from adafruit_bus_device.spi_device import SPIDevice



CHIP_SELECT = digitalio.DigitalInOut(board.GP17)
LCD_RESET = digitalio.DigitalInOut(board.GP16)

SPI_BAUD_RATE = const(1_100_000)

DISPLAY_HEIGHT = const(64)
DISPLAY_WIDTH = const(128)


class PiPico_SPI_LCD:
    """A container class to create the SPI device object."""

    def __init__(self):
        spi = busio.SPI(board.GP18, MOSI=board.GP19)

        # this is mini hack so that we don't need to enter a
        # context manager at the top level. Doesn't look nice.
        self.spi_bus = spi.__enter__()
        self.spi_device = SPIDevice(self.spi_bus,
                                    CHIP_SELECT,
                                    cs_active_value=True,
                                    baudrate=SPI_BAUD_RATE)

        self.display = ST7920(self.spi_device, width=DISPLAY_WIDTH,
                              height=DISPLAY_HEIGHT, reset=LCD_RESET)

    def clear_framebuffer(self):
        self.display.clear_framebuffer()

    def clear_display(self):
        self.display.clear_display()

    def show(self):
        self.display.show()
