#!/bin/bash
set -e
set -u

usage=(
  "fetch_tools has no real interface, it simply fetches depot_tools with git at the specified version."
  ""
  "Usage (DO NOT USE --long-flags=something, just --long-flag something):"
  "You can always try -v or --verbose"
  ""
  "Display this help:"
  "fetch_tools [-h|--h]"
  ""
  "Delete .git to save space:"
  "fetch_tools [-d|--delete-git]"
  ""
  ""
)


FLAGS=("-d" "--delete-git")
ARGFLAGS=()

SCRIPT_DIR="$( cd -- "$( dirname -- $(readlink -f -- "${BASH_SOURCE[0]}") )" &> /dev/null && pwd )"
. "$SCRIPT_DIR/include/utilities.sh"

DELETE_GIT="$(flags_resolve false "-d" "--delete-git")" # will resolve true if existing, false if no

$NO_VERBOSE || echo "Running 01-fetch_tools.sh"

util_get_version
util_export_version

# Get depot_tools
$NO_VERBOSE || echo "Downloading depot_tools:"
git clone https://chromium.googlesource.com/chromium/tools/depot_tools.git "$MAIN_DIR/vendor/depot_tools/"

$NO_VERBOSE || echo "Resetting depot_tools:"
git -C "$MAIN_DIR/vendor/depot_tools/" reset --hard ${DEPOT_TOOLS_COMMIT}
$NO_VERBOSE || echo "Cleaning depot_tools:"
git -C "$MAIN_DIR/vendor/depot_tools/" clean -ffd

if $DELETE_GIT; then
  $NO_VERBOSE || echo "Deleting depot_tools/.git"
  rm -rf "$MAIN_DIR/vendor/depot_tools/.git" # oof dangerous
fi
