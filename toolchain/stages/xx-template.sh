#!/bin/bash

set -e
set -u
# Please do your flags first so that utilities uses $NO_VERBOSE, otherwise failure!

SCRIPT_DIR=$( cd -- "$( dirname -- $(readlink -f -- "${BASH_SOURCE[0]}") )" &> /dev/null && pwd )
. "$SCRIPT_DIR/include/utilities.sh"

get_version
export_version

