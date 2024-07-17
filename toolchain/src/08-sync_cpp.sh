#!/bin/bash
set -e
set -u

usage=(
  "sync_cpp will copy kaleido c++ source in chromium source for build"
  "it uses rsync to preserver modification times and no unnecessary update things"
  ""
  ""
  "Usage (DO NOT USE --long-flags=something, just --long-flag something):"
  "You can always try -v or --verbose"
  ""
  "Try: Will use the latest version's patch dir if it can't find its own"
  "sync_cpp [-t|--try]"
  ""
)

FLAGS=("-t" "--try")
ARGFLAGS=()

SCRIPT_DIR="$( cd -- "$( dirname -- $(readlink -f -- "${BASH_SOURCE[0]}") )" &> /dev/null && pwd )"
. "$SCRIPT_DIR/include/utilities.sh"

$NO_VERBOSE || echo "Running 08-sync_cpp.sh"

util_get_version
util_export_version

CC_DIR="${MAIN_DIR}/src/kaleido/cc/$CHROMIUM_VERSION_TAG"
if [ ! -d "$CC_DIR" ] && $TRY; then
  CC_DIR="${MAIN_DIR}/src/kaleido/cc/$(ls "${MAIN_DIR}/src/kaleido/cc/" -vt | head -1)"
elif [ -d "$CC_DIR" ]; then
  : # optimistic path
else
  util_error "No cc dir for $CHROMIUM_VERSION_TAG, look at --try or make your own"
fi


rsync -av --delete "${CC_DIR}/" "${MAIN_DIR}/vendor/src/headless/app"
