# TFI Bus Stop Display

This project contains the microcontroller code to build an LCD display to show Live Departure times of busses, using the **Transport for Ireland** data backend. 

## Hardware BOM

- 128x64 LCD Display that uses an ST7920 controller: https://de.aliexpress.com/item/1005006293405422.html
- Raspberry Pi Pico W

## Software

You'll need a running instance of the following Docker container, which manages the data source from TFI: [TFI GTFS](https://github.com/seanblanchfield/tfi-gtfs)

### Micropython

