#!/bin/bash

# board location
BOARD="/Volumes/TFI-DISPLAY"

# compile all libraries to byte code before upload to the board.
COMPILE_ALL="yes"

# set the optimisation level for the byte code compilation
# set this to 3 to strip the line numbers from tracebacks
# 	http://docs.micropython.org/en/latest/library/micropython.html#micropython.opt_level
COMPILE_OPT_LEVEL=2

# when compiling the modules, logging can also be stripped from
# the file before the compilation. Choose that here:
COMPILE_STRIP_LOGGING="yes"


if [ ! -d "$BOARD" ]; then
	echo "ERROR: board does not exist at '$BOARD'"
	exit 1
fi

function fullpath () {
	python3 -c "import os,sys; print(os.path.realpath(sys.argv[1]))" $1
}

# full path to the location of the current dir
rel_dir="`dirname "$0"`"
full_dir="`fullpath "$rel_dir"`"


MPYCROSS="$full_dir/mpy-cross"

if [ "$COMPILE_ALL" == "yes" ]; then
	
	# make sure the `mpy-cross` executable is available
	if [ -! -e "$MPYCROSS" ]; then
		echo "mpy-cross could not be found - download it from Adafruit at:"
		echo "    https://adafruit-circuit-python.s3.amazonaws.com/index.html?prefix=bin/mpy-cross/"
		echo ""
		echo "Choose a file from the OS folders at the top, not the parent listing."
		echo "The version should match the CircuitPython version (see $BOARD/boot_out.txt)"
		echo "Rename that file to 'mpy-cross', and give it executable permissions."
		echo "Clean any com.apple.quarantine attributes with 'xattr -c'."
		echo ""
		exit 1
	fi

	tmp_dir=$(mktemp -d -t ci-XXXXXXXXXX)

	# copy all the files to a temp location
	rsync -ar "$full_dir/../src_uC/" "$tmp_dir/" >/dev/null 2>/dev/null

	# jump to the library folder and attempt to compile all the files
	pushd "$tmp_dir/lib" >/dev/null 2>/dev/null
	for f in *.py; do
		echo "Compiling: $f"

		# first clean all the logging statements from the file
		# if [ "$COMPILE_STRIP_LOGGING" == "yes" ]; then
		# 	python3 "$full_dir/sanitise.py" "$f"
		# fi

		$MPYCROSS -O$COMPILE_OPT_LEVEL "$f"
		rm "$f"
	done

	popd >/dev/null 2>/dev/null

	# now transfer over all the files to the target
	rsync -arv --delete "$tmp_dir/" "$BOARD" 2>/dev/null

	# erase the temp folder
	rm -rf "$tmp_dir"
else

	echo "Attempting to upload all code to the board..." 

	rsync -arv --delete "$full_dir/../src_uC/" "$BOARD"

fi