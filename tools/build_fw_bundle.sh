#!/bin/bash

#
# this script will build a micropython firmware file, plus the code files
# from the repo, that will be packaged up into a single UF2.
#
# This requires all of the micropython build tools to be available, and
# compiling micropython from source, so not for the feint of heart!
#

function fullpath () { python3 -c "import os,sys; print(os.path.realpath(sys.argv[1]))" $1 }

# full path to the location of the current dir
rel_dir="`dirname "$0"`"
full_dir="`fullpath "$rel_dir"`"

