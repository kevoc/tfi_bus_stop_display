
from st7920_display import ST7920

import board
import busio
import digitalio

from adafruit_bus_device.spi_device import SPIDevice


with busio.SPI(board.GP18, MOSI=board.GP19) as spi_bus:
    cs = digitalio.DigitalInOut(board.GP17)
    reset = digitalio.DigitalInOut(board.GP16)

    device = SPIDevice(spi_bus, cs, cs_active_value=True, baudrate=1_000_000)

    display = ST7920(device, width=128, height=64, reset=reset)

    display.clear_display()

    display.fill_rect(20, 20, 20, 20, 1)
    display.fill_rect(25, 25, 10, 10, 0)

    display.show()
