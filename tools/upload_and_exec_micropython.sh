#!/bin/bash


# board location
BOARD="`ls /dev/tty.usbmodem*`"

# compile all libraries to byte code before upload to the board.
COMPILE_ALL="yes"

# set the optimisation level for the byte code compilation
# set this to 3 to strip the line numbers from tracebacks
# 	http://docs.micropython.org/en/latest/library/micropython.html#micropython.opt_level
COMPILE_OPT_LEVEL=2

# target architecture is required to allow for native and viper emitters
TARGET_ARCH=armv6m
COMPILE_FLAGS="-X emit=native"

# Using the native emitter uses ~5% more ram:
#    emit=native -> Total:189952 Free:155792 (82.02%)
#    none        -> Total:189952 Free:165488 (87.12%)

if [ ! -e "$BOARD" ]; then
	echo "ERROR: board not found '$BOARD'"
	exit 1
fi

function fullpath () {
	python3 -c "import os,sys; print(os.path.realpath(sys.argv[1]))" $1
}

# full path to the location of the current dir
rel_dir="`dirname "$0"`"
full_dir="`fullpath "$rel_dir"`"


# you need to install the mpy-cross version specific for your
# version of micrpython: https://github.com/pybricks/python-mpy-cross
# 	pip install mpy-cross-v6.3
MPYCROSS="mpy-cross-v6.3"


if [ "$COMPILE_ALL" == "yes" ]; then
	
	# make sure the `mpy-cross` executable is available
	if [ -z "`which "$MPYCROSS"`" ]; then
		echo "mpy-cross could not be found!"
		echo "Install it from PyPi."
		echo ""
		exit 1
	fi

	tmp_dir=$(mktemp -d -t ci-XXXXXXXXXX)

	# copy all the files to a temp location
	rsync -ar "$full_dir/../src_uC/" "$tmp_dir/" >/dev/null 2>/dev/null

	# jump to the temporary folder and attempt to compile all the files
	pushd "$tmp_dir/" >/dev/null 2>/dev/null
	
	# compile the micropython files to .mpy and delete the originals
	# -mindepth=2 so that root level files (like main.py and boot.py) never get compiled.
	echo ""
	echo "Compiling .py files..."
	find . -name "*.py" -mindepth 2 -print -exec "$MPYCROSS" -march=$TARGET_ARCH $COMPILE_FLAGS -O$COMPILE_OPT_LEVEL '{}' \;
	find . -name "*.py" -mindepth 2 -delete
	
	# # erase the temp folder
	# rm -rf "$tmp_dir"


else
	# jump to the source dir
	pushd "$full_dir/../src_uC/" >/dev/null 2>/dev/null
	
fi


echo ""
echo 'Erasing all files on the MicroPython...'
ampy -p "$BOARD" rmdir '/' >/dev/null 2>/dev/null



# Upload all files using the ampy tool
# 		pip3 install adafruit-ampy --upgrade --break-system-packages


echo ""
echo 'Uploading all files from:'
echo -n '    '
pwd

# create all folders first
find . -type d -mindepth 1 -print -exec ampy -p "$BOARD" mkdir '{}' \;

# upload the files
find . -type f -not -name '.DS_Store' -print -exec ampy -p "$BOARD" put '{}' '{}' \;

popd >/dev/null 2>/dev/null


echo ""
echo 'Launching a serial terminal... (press Ctrl+D to restart uPy)'
echo ''

python3 -m serial.tools.miniterm --raw "$BOARD" 115200
