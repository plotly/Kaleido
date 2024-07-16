#!/bin/bash
set -e
set -u

# TODO: add --check and --stat, and defaults

usage=(
  "append_gn will append a build directive to the headless gn configuration."
  "we originally only do this in windows, I'm not sure why, and I believe the gn gen"
  "line would do it automatically, so we should test remove it by trial and error."
  "Furthermore, this patch will probably have to be adjust by version."
  ""
  "Usage (DO NOT USE --long-flags=something, just --long-flag something):"
  "You can always try -v or --verbose"
)
## PROCESS FLAGS

FLAGS=()
ARGFLAGS=()

SCRIPT_DIR=$( cd -- "$( dirname -- $(readlink -f -- "${BASH_SOURCE[0]}") )" &> /dev/null && pwd )
. "$SCRIPT_DIR/include/utilities.sh"

$NO_VERBOSE || echo "Running 06-append_gn.sh"

util_get_version
util_export_version

PATCH="$MAIN_DIR/toolschain/gn_append.patch"

echo "THIS NEEDS TO BE INSPECTED. IS IT NECESSARY? WHY ONLY ON WINDOWS?"
if [[ "$PLATFORM" == "WINDOWS" ]]; then
  git -C $MAIN_DIR/vendor/src apply --check --reverse "$PATCH" && echo "Patch seems to be already applied" && exit 0 || true
  git -C $MAIN_DIR/vendor/src apply "$PATCH"
fi
