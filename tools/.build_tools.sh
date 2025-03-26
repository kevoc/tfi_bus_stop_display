#!/bin/bash

# board location
BOARD_TTY="`ls /dev/tty.usbmodem*`"
BOARD_CU="`ls /dev/cu.usbmodem*`"

# let ampy know the board to use
export AMPY_PORT="$BOARD_TTY"


# you need to install the mpy-cross version specific for your
# version of micropython: https://github.com/pybricks/python-mpy-cross
# 	pip install mpy-cross-v6.3
MPYCROSS="mpy-cross-v6.3"


# set the optimisation level for the byte code compilation
# set this to 3 to strip the line numbers from tracebacks
# 	http://docs.micropython.org/en/latest/library/micropython.html#micropython.opt_level
COMPILE_OPT_LEVEL=2

# target architecture is required to allow for native and viper emitters
# this is the architecture for Raspberry Pi Pico
TARGET_ARCH=armv6m
COMPILE_FLAGS=""   # "-X emit=native"

# Using the native emitter uses ~5% more ram:
#    emit=native -> Total:189952 Free:155792 (82.02%)
#    none        -> Total:189952 Free:165488 (87.12%)
#
# It's not a good idea to enable the native emitter with "-X emit=native"
# to compile everything to native. If a python exception is thrown at startup
# your firmware will be bricked. It never exits to the REPL. You need to
# install the "nuke_flash.uf2" and then micropython again to recover the board.
#

function assert_board_connected () {
  # exit if the discovered board doesn't exist.
  if [ ! -e "$BOARD_TTY" -o ! -e "$BOARD_CU" ]; then
    echo "ERROR: board not found '$BOARD_TTY'"
    exit 1
  fi
}


function compile_dir() {
  # $1 - the directory of python files to non-destructively compile to byte code
  # $2 - the destination directory for the compiled bundle
  # $3 - starting directory depth - default 1 (i.e. full folder). Usually, you'll
  #      set this to 2, which will only compile .py files in sub-folders, leaving
  #      parent folder .py files (like main.py and boot.py) un-compiled
  #
  # Note: the destination folder "$2" will also have the un-compiled .py files
  #       that weren't compiled due to the $3 preference.

  SOURCE_DIR="$1"
  DEST_DIR="$2"
  START_DEPTH="${3:-1}"   # arg 3: default=1 if unspecified

  # make sure the `mpy-cross` executable is available
	if [ -z "`which "$MPYCROSS"`" ]; then
		echo "mpy-cross could not be found!"
		echo "Install it from PyPi."
		echo ""
		exit 1
	fi

	# copy all the files to a temp location
	rsync -ar "$SOURCE_DIR/" "$DEST_DIR/" >/dev/null 2>/dev/null

	# jump to the desitination folder and attempt to compile all the files
	pushd "$DEST_DIR/" >/dev/null 2>/dev/null

	# compile the micropython files to .mpy and delete the originals
	echo ""
	echo "Compiling .py files..."
	find . -name "*.py" -mindepth $START_DEPTH -print -exec "$MPYCROSS" -march=$TARGET_ARCH $COMPILE_FLAGS -O$COMPILE_OPT_LEVEL '{}' \;
	find . -name "*.py" -mindepth $START_DEPTH -delete

  # restore the working directory
  popd >/dev/null 2>/dev/null

}

