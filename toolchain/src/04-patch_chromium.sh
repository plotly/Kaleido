#!/bin/bash
set -e
set -u

usage=(
  "patch_chromium will run patches stored in the patches/ folder."
  "patch needs for a particular version may change over time."
  "directory for the particular version of the software."
  ""
  "Usage (DO NOT USE --long-flags=something, just --long-flag something):"
  "You can always try -v or --verbose"
  ""
  "Try: Will use the latest version's patch dir if it can't find its own"
  "patch_chromium [-t|--try]"
  ""
  ""
)
## PROCESS FLAGS

FLAGS=("-t" "--try")
ARGFLAGS=()

SCRIPT_DIR="$( cd -- "$( dirname -- $(readlink -f -- "${BASH_SOURCE[0]}") )" &> /dev/null && pwd )"
. "$SCRIPT_DIR/include/utilities.sh"

TRY="$(flags_resolve false "-t" "--try")"

util_get_version
util_export_version

$NO_VERBOSE || echo "Running 04-patch_chromium"

PATCH_DIR="$MAIN_DIR/src/vendor-patches/chromium/$CHROMIUM_VERSION_TAG"
if [ ! -d "$PATCH_DIR" ] && $TRY; then
  PATCH_DIR="$MAIN_DIR/src/vendor-patches/chromium/$(ls $MAIN_DIR/src/vendor-patches/chromium -vt | head -1)"
elif [ -d "$PATCH_DIR" ]; then
  : # optimistic path
else
  util_error "No chromium patch dir for $CHROMIUM_VERSION_TAG, look at --try or make your own"
fi

if [ -d "$PATCH_DIR" ] && [ -e "$PATCH_DIR/*.patch" ]; then
  git -C $MAIN_DIR/vendor/src/ apply $PATCH_DIR/*.patch
fi
