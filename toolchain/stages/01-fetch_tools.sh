#!/bin/bash

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd ) # stolen from stack exchange
. "$SCRIPT_DIR/include/utilities.sh"

util_get_version
util_export_version

# Get depot_tools
git clone https://chromium.googlesource.com/chromium/tools/depot_tools.git "$MAIN_DIR/repos/depo_tools/"

git -C "$MAIN_DIR/repos/depot_tools/" reset --hard ${DEPOT_TOOLS_COMMIT}
git -C "$MAIN_DIR/repos/depot_tools/" clean -ffd

