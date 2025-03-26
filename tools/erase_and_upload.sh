#!/bin/bash

# compile all libraries to byte code before upload to the board.
COMPILE_ALL="yes"

# a file to store the list of MD5 hashes of files, to know what's
# been downloaded to the board already.
DOWNLOADED="build/.board_files"

# filters to apply to `find` commands to
FIND_FILTERS="-not -name .DS_Store -not -name *.sample"


# load the other build tools
source "tools/.build_tools.sh"


if [ "$COMPILE_ALL" == "yes" ]; then
	# clear out the build folder
	rm -rf "build/src_uC/" 2>/dev/null
	mkdir -p "build/src_uC"

  compile_dir "src_uC/" "build/src_uC" 2
  UPLOAD_FROM="build/src_uC"
else
	UPLOAD_FROM="src_uC"
fi


echo ""
echo "Grabbing any logs on the device before erase..."
source "tools/grab_logs.sh"


echo ""
echo 'Erasing all files on the MicroPython board...'
ampy rmdir '/' >/dev/null 2>/dev/null


# Upload all files using the ampy tool
# 		pip3 install adafruit-ampy --upgrade --break-system-packages


echo ""
echo 'Uploading all files from:'
echo -n '    '
pwd
echo ""

find "$UPLOAD_FROM" -type f $FIND_FILTERS -print | while read build_file; do

  # the target file has the first N characters trimmed off, the exact
  # length of the UPLOAD_FROM path length.
  path_on_device="${build_file:${#UPLOAD_FROM}}"
  parent_folder_on_device="`dirname "$path_on_device"`"

  echo "    -> $path_on_device"

  # create the folder and upload the file
  ampy mkdir "$parent_folder_on_device" 2>/dev/null
  ampy put "$build_file" "$path_on_device"

done


# create a listing of all md5 hashes of the files sent to the board
# for use next time to know what not to send.
find "$UPLOAD_FROM" -type f $FIND_FILTERS -exec openssl md5 -r '{}' + > "$DOWNLOADED"


echo ""
echo "Soft reboot MicroPython..."
printf '\x04' > "$BOARD_CU"

