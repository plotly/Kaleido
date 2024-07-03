#!/bin/bash

usage=(
  "fetch_tools has no interface, it simply fetches depot_tools with git at the specified version."
  ""
  "Usage (DO NOT USE --long-flags=something, just --long-flag something):"
  "You can always try -v or --verbose"
  ""
  "Display this help:"
  "set_version [-h|--h]"
)
## PROCESS FLAGS

NO_VERBOSE=true
while (( $# )); do
  case $1 in
    -h|--help)      printf "%s\n" "${usage[@]}"; exit 0  ;;
    -v|--verbose)   NO_VERBOSE=false                     ;;
    *)              printf "%s\n" "${usage[@]}"; exit 1  ;;
  esac
  shift
done

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd ) # stolen from stack exchange
. "$SCRIPT_DIR/include/utilities.sh"

util_get_version
util_export_version

# Get depot_tools
$NO_VERBOSE || echo "Downloading depot_tools:"
git clone https://chromium.googlesource.com/chromium/tools/depot_tools.git "$MAIN_DIR/repos/depo_tools/"

$NO_VERBOSE || echo "Resetting depot_tools:"
git -C "$MAIN_DIR/repos/depot_tools/" reset --hard ${DEPOT_TOOLS_COMMIT}
$NO_VERBOSE || echo "Cleaning depot_tools:"
git -C "$MAIN_DIR/repos/depot_tools/" clean -ffd

