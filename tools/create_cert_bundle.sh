#!/bin/bash


source "tools/.build_tools.sh"


# the location of the logs folder on the device.
BOARD_LOG_FOLDER='logs'


function grab_logs () {
  # download all log files from the logs folder on the device.

  # create the local logs folder
  mkdir "logs" 2>/dev/null

  # get a list of all files to grab
  ampy ls "$BOARD_LOG_FOLDER" >/tmp/micropython-log-files.txt

  while read -u 10 log; do
    echo "Grabbing log file: $log"
    ampy get "$log" "logs/`basename "$log"`"
  done 10</tmp/micropython-log-files.txt

}

grab_logs