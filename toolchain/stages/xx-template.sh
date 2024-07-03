#!/bin/bash

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd ) # stolen from stack exchange
. "$SCRIPT_DIR/include/utilities.sh"

get_version
export_version

