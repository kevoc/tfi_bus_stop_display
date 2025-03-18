import board
import st7920

import busio
import digitalio

from adafruit_bus_device.spi_device import SPIDevice

with busio.SPI(board.GP18, MOSI=board.GP19) as spi_bus:
    cs = digitalio.DigitalInOut(board.GP17)
    device = SPIDevice(spi_bus, cs, cs_active_value=True, baudrate=1000000)

    screen = st7920.Screen(device, slaveSelectPin=cs)

    def clear():
        screen.clear()
        screen.redraw()

    def draw():

        # write zeroes to the buffer
        screen.clear()

        for mv in screen.fbuff:
            for i in range(len(mv)):
                mv[i] = 0b10101010

        # draw some points, lines, rectangles, filled rectangles in the buffer
        # screen.plot(5, 5)
        # screen.line(10, 10, 15, 15)
        # screen.rect(20, 20, 25, 25)
        # screen.fill_rect(30, 30, 40, 40)
        # screen.fill_rect(32, 32, 38, 38, False)

        # send the buffer to the display
        screen.redraw()

    def run():
        clear()
        draw()
    

    run()