#!/bin/bash
set -e
set -u

# TODO: add --check and --stat, and defaults

usage=(
  "patch_chromuium will run patches stored in the patches/ folder."
  "patch needs for a particular version may change over time."
  "directory for the particular version of the software."
  ""
  "Usage (DO NOT USE --long-flags=something, just --long-flag something):"
  "You can always try -v or --verbose"
)
## PROCESS FLAGS

FLAGS=()
ARGFLAGS=()

SCRIPT_DIR=$( cd -- "$( dirname -- $(readlink -f -- "${BASH_SOURCE[0]}") )" &> /dev/null && pwd )
. "$SCRIPT_DIR/include/utilities.sh"

$NO_VERBOSE || echo "Running 04-patch_chromium"

PATCH_DIR="$MAIN_DIR/patches/chromium/$CHROMIUM_VERSION_TAG"
if [ -d "" ]; then
  for patch in $(find $PATCH_DIR -name '*.patch'); do
    git apply $patch
  done
else
  mkdir -p "$MAIN_DIR/patches/chromium/$CHROMIUM_VERSION_TAG"
  $NO_VERBOSE || echo "No patches found for $CHROMIUM_VERSION_TAG, creating directory."
fi