# TFI Bus Stop Display

This project contains the server-side and microcontroller code to build an LCD display to show Bus Stop timetables, using the **Transport for Ireland** data backend. 

For this project, you'll need a running instance of the following Docker container, which manages the data source from TFI: [TFI GTFS](https://github.com/seanblanchfield/tfi-gtfs)

This project uses CircuitPython running on a Pi Pico W, with a 128x64 LCD display, which uses an ST7920 controller in serial SPI mode. 

