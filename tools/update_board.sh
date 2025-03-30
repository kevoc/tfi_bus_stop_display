#!/bin/bash

# compile all libraries to byte code before upload to the board.
COMPILE_ALL="yes"

# a file to store the list of MD5 hashes of files, to know what's
# been downloaded to the board already.
DOWNLOADED="build/.board_files"

# filters to apply to `find` commands to
FIND_FILTERS="-not -name .DS_Store -not -name *_sample.cfg"


# load the other build tools
source "tools/.build_tools.sh"


assert_board_connected

# make the build folder in case it doesn't exist
mkdir "build"  2>/dev/null

# compile the files if required
if [ "$COMPILE_ALL" == "yes" ]; then
	# clear out the build folder
	rm -rf "build/src_uC/" 2>/dev/null
	mkdir -p "build/src_uC"

  compile_dir "src_uC/" "build/src_uC" 2
  UPLOAD_FROM="build/src_uC"
else
	UPLOAD_FROM="src_uC"
fi


# loop through all files, uploading any changed files
echo ""
echo "Updating board files (only if required)..."
find "$UPLOAD_FROM" -type f $FIND_FILTERS -print | while read build_file; do

  # get the saved hash from the previous run
  last_md5hash=`grep -F "$build_file" "$DOWNLOADED" 2>/dev/null | awk '{print $1}'`

  # get the current hash of this file
  current_md5hash=`md5 -q "$build_file"`

  # if there's a mis-match, download the new file to the board
  if [ "$last_md5hash" != "$current_md5hash" ]; then
    # the target file has the first N characters trimmed off, the exact
    # length of the UPLOAD_FROM path length.
    path_on_device="${build_file:${#UPLOAD_FROM}}"
    parent_folder_on_device="`dirname "$path_on_device"`"

    echo "$path_on_device"

    # if this folder doesn't exist in the history, create it.
    if ! grep -F "$parent_folder_on_device" "$DOWNLOADED" >/dev/null 2>/dev/null; then
      ampy mkdir "$parent_folder_on_device"
      if [ $? -ne 0 ]; then echo "ERROR while making parent folder on device."; exit 1; fi
    fi

    # upload the file
    ampy put "$build_file" "$path_on_device"
    if [ $? -ne 0 ]; then echo "ERROR while uploading file to device."; exit 1; fi
  fi

done

if [ $? -ne 0 ]; then
  # because the while loop above gets the list of files piped into
  # it, the while loop is launched in a subshell. This means the
  # exit commands in the if statements only exit the subshell. This
  # check will exit the main shell if the last subshell exited with
  # an error.
  exit 1
fi


# create a listing of all md5 hashes of the files sent to the board
# for use next time to know what not to send.
find "$UPLOAD_FROM" -type f $FIND_FILTERS -exec openssl md5 -r '{}' + > "$DOWNLOADED"



echo ""
echo "Soft reboot MicroPython..."
printf '\x04' > "$BOARD_CU"

