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
)

FLAGS=()
ARGFLAGS=()

SCRIPT_DIR=$( cd -- "$( dirname -- $(readlink -f -- "${BASH_SOURCE[0]}") )" &> /dev/null && pwd )
. "$SCRIPT_DIR/include/utilities.sh"

$NO_VERBOSE || echo "Running 08-sync_cpp.sh"

util_get_version
util_export_version


rsync -av --delete ${MAIN_DIR}/src/kaleido/cc-${CHROMIUM_VERSION_TAG}/ ${MAIN_DIR}/vendor/src/headless/app
