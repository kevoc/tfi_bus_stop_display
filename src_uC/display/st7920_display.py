
"""
`st7920_display`
====================================================

Circuit Python driver for ST7920 LCD display, using SPI interface

* Author: Kevin O'Connell

Based on `adafruit_ssd1306` driver by Tony DiCola, Michael McWethy,
and using the `adafruit_framebuf` graphic stack.

"""

import time

from machine import Pin
from micropython import const
from framebuf import FrameBuffer, MONO_HLSB



try:
    # Used only for typing
    from typing import Optional, Union, List
except ImportError:
    pass


# instruction constants to be written to the instruction register
_DISPLAY_CLEAR = const(0x01)
_ADDRESS_COUNTER_HOME = const(0x02)
_ENTRY_MODE = const(0x04)
_DISPLAY_CONTROL = const(0x08)


@micropython.native
def encode_for_spi_tx(input_buf: memoryview, output_buf: memoryview):
    """Convert the bytes in the input buffer to the format required
    for SPI transmission, and place them in the output buffer."""

    for i, byte in enumerate(input_buf):
        output_buf[2 * i] = byte & 0xF0
        output_buf[(2 * i) + 1] = (byte & 0x0F) << 4


class ST7920(FrameBuffer):
    """Base class for SSD1306 display driver"""

    def __init__(self, spi, width: int, height: int, chip_select: Pin,
                 reset: Optional[Pin] = None):

        self.spi = spi
        self.width = width
        self.height = height

        # the frame buffer will hold the active generated frame
        frame_buffer_size = (width // 8) * height
        self.framebuf = memoryview(bytearray(frame_buffer_size))

        # the spi buffer needs to be double the size of frame buffer because
        # each bytes is encoded as 2 bytes, plus 1 header byte.
        self.spi_buffer = memoryview(bytearray((2 * frame_buffer_size) + 1))

        # this instruction scratch register will hold the instruction
        # bytes before being formatted for transmission.
        self.instruction_scratch = memoryview(bytearray(2))

        super().__init__(memoryview(self.framebuf),
                         width, height, MONO_HLSB)

        self.reset_pin = reset
        self.chip_select = chip_select

        self.initialise_display()

    def initialise_display(self):
        """Send the init byte sequence to configure the display."""

        # This sequence is taken from page 34 of the datasheet
        self.reset()

        # send the initial config twice, per the datasheet power up sequence
        for _ in range(2):
            self.configure_op_modes(eight_bit=1, extended_instr=0, graphic=0)
            time.sleep(100.0e-6)

        self.configure_display_control(display=1, cursor=0, blink=0)
        time.sleep(100.0e-6)

        self.configure_op_modes(eight_bit=1, extended_instr=1, graphic=0)
        time.sleep(100.0e-6)

        self.configure_op_modes(eight_bit=1, extended_instr=1, graphic=1)

        self.clear_display()
        time.sleep(10.0e-3)

    def reset(self):
        """If a reset pin was provided, pulse it low"""

        if self.reset_pin is not None:
            # put the display into reset for 50ms.
            self.reset_pin.init(Pin.OUT)
            self.reset_pin.value(0)
            time.sleep(0.05)
            self.reset_pin.init(Pin.IN)  # high Z
            time.sleep(0.05)  # datasheet specifies min. 40ms wait after reset

    def _write_buffer(self, buffer: memoryview):
        """Write the given buffer to the SPI device"""

        try:
            self.chip_select.value(1)
            self.spi.write(buffer)
        finally:
            self.chip_select.value(0)

    def write(self, RS, RW, command: Union[int, List[int], memoryview]):
        """Write an arbitrary command to the display."""

        # Each command sent to the display is 10 bits.
        #   - Two bits called RS and RW, defining the instruction type, (see
        #     page 10 of the datasheet)
        #
        #         RS   RW
        #         0    0    MPU write instruction to instruction register (IR)
        #         0    1    MPU read busy flag (BF) and address counter (AC)
        #         1    0    MPU write data to data register (DR)
        #         1    1    MPU read data from data register (DR)
        #
        #   - and an 8 bit command byte
        #
        # These 10 bits are split across 3 bytes when sent over SPI:
        #   byte 0:    five MSBs=1 "synchronising", bit 2 = RW, bit 1 = RS, bit 0 = 0
        #   byte 1:    four MSBs=four MSBs of the 8 bit instruction (bits 7-4)
        #   byte 2:    four MSBs=four LSBs of the 8 bit instruction (bits 3-0)
        #
        # If multiple bytes are being sent, each one needs to be split into an
        # upper nibble and lower nibble and sent as 2 bytes, as described above.

        # synchronising bits, plus RW and RS
        self.spi_buffer[0] = 0b11111000 | (RW << 2) | (RS << 1)

        if isinstance(command, int):
            self.instruction_scratch[0] = command
            encode_for_spi_tx(self.instruction_scratch[:1], self.spi_buffer[1:])
            self._write_buffer(self.spi_buffer[:3])

        elif isinstance(command, list):
            size = len(command)
            #print(f'got list of bytes: {command}')
            self.instruction_scratch[:] = bytes(command)
            encode_for_spi_tx(self.instruction_scratch[:size], self.spi_buffer[1:])
            self._write_buffer(self.spi_buffer[:1 + (2 * size)])

        else:     # this is a memory view
            size = len(command)
            encode_for_spi_tx(command, self.spi_buffer[1:])
            self._write_buffer(self.spi_buffer[:1 + (2 * size)])

    def write_instruction_register(self, instruction: Union[int, List[int]]):
        """Write the given instruction to the display"""
        self.write(RS=0, RW=0, command=instruction)

    def write_data_register(self, data: memoryview):
        """Write the given instruction to the display"""
        self.write(RS=1, RW=0, command=data)

    def set_display_address(self, vertical: int, horizontal: int):
        """Set the Graphic Display RAM address, `vertical` is the vertical row
        of the display, `horizontal` is the horizontal byte offset along the row,
        i.e. a block of 8 pixels."""
        self.write_instruction_register([(0x80 | vertical), (0x80 | horizontal)])

    def set_display_address_to_home(self):
        """Set the Graphic Display RAM address to the home position."""
        self.write_instruction_register(_ADDRESS_COUNTER_HOME)

    def configure_op_modes(self, eight_bit: int, extended_instr: int, graphic: int):
        """Send a operation mode configuration byte."""

        # From the datasheet:
        #   DL: 4/8-bit interface control bit
        #       When DL = "1", 8-bit MPU interface.
        #       When DL = "0", 4-bit MPU interface.
        #   RE: extended instruction set control bit
        #       When RE = "1", extended instruction set
        #       When RE = "0", basic instruction set
        #   G: Graphic display control bit
        #       When G = "1", Graphic Display ON
        #       When G = "0", Graphic Display OFF

        self.write_instruction_register(0x20 | (eight_bit << 4) |
                                               (extended_instr << 2) |
                                               (graphic << 1))

    def configure_display_control(self, display: int, cursor: int, blink: int):
        """Send a display control configuration byte."""

        # From the datasheet:
        #   D: Display ON/OFF control bit
        #       When D = "1", display ON
        #       When D = "0", display OFF, the content of DDRAM is not changed
        #   C: Cursor ON/OFF control bit
        #       When C = "1", cursor ON.
        #       When C = "0", cursor OFF.
        #   B: Character Blink ON/OFF control bit
        #       When B = "1", cursor position blink ON. Then display data (character) in cursor position will blink.
        #       When B = "0", cursor position blink OFF

        self.write_instruction_register(_DISPLAY_CONTROL | (display << 2) |
                                                           (cursor << 1) |
                                                            blink)

    def configure_direction(self, address_counter_inc: int, shift: int):
        """Send the address counter increment/decrement bit, controlling whether
        the display is drawn left-to-right, and which direction shifts go."""

        # From the datasheet:
        #   I/D: Address Counter Control: (Increase/Decrease)
        #       When I/D = "1", cursor moves right, address counter (AC) is increased by 1.
        #       When I/D = "0", cursor moves left, address counter (AC) is decreased by 1.
        #   S: Display Shift Control: (Shift Left/Right)
        #       When I/D = "1", S = "1": Entire display shift left by 1
        #       When I/D = "1", S = "0": Entire display shift right by 1

        self.write_instruction_register(_ENTRY_MODE | (address_counter_inc << 1) | shift)

    def clear_framebuffer(self):
        """Zero out all bytes in the frame buffer."""

        # zero out the frame buffer
        self.fill(0)

    def clear_display(self):
        """Send the command to clear the display."""

        self.clear_framebuffer()
        self.write_instruction_register(_DISPLAY_CLEAR)

    def show(self) -> None:
        """Write the full frame buffer to the device."""

        # The frame buffer doesn't map directly to display RAM on the
        # LCD. The LCD ram is laid out as 256x32 even though the display
        # is 128 wide x 64 high.
        #
        # All lines map as follows:
        #   byte 0 is left-most on display, MSB of each byte is left-most pixel
        #
        # The data can only be sent in blocks of 16 bytes, from the datasheet:
        #   After the horizontal address reaching 0FH, the horizontal address
        #   will be set to 00H and the vertical address will not change.
        #
        # Therefore changing the layout of the framebuffer won't allow the
        # data to be sent in one large block because the vertical address doesn't
        # increment.
        #

        for line_index in range(self.height):
            self.set_display_address(line_index & 0x1F, 8 * (line_index >> 5))
            self.write_data_register(self.framebuf[line_index * 16:(line_index * 16) + 16])
