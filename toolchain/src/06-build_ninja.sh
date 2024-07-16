#!/bin/bash
set -e
set -u

usage=(
  "build_ninja will run modify and run gn, the last build step before actual chromium build."
  "It appends information about our app to the gn configuration in src/headless."
  ""
  ""
  "Usage (DO NOT USE --long-flags=something, just --long-flag something):"
  "You can always try -v or --verbose"
  ""
  "TODO: add check, list, etc"
)
## PROCESS FLAGS

FLAGS=()
ARGFLAGS=()

SCRIPT_DIR=$( cd -- "$( dirname -- $(readlink -f -- "${BASH_SOURCE[0]}") )" &> /dev/null && pwd )
. "$SCRIPT_DIR/include/utilities.sh"

$NO_VERBOSE || echo "Running 06-build_ninja.sh"

util_get_version
util_export_version

PATCH="$MAIN_DIR/toolschain/gn_append.patch"

$NO_VERBOSE || echo "Appending build information to headless/BUILD.gn"
echo "THIS NEEDS TO BE INSPECTED. IS IT NECESSARY? WHY ONLY ON WINDOWS?"
if [[ "$PLATFORM" == "WINDOWS" ]]; then
  git -C $MAIN_DIR/vendor/src apply --check --reverse "$PATCH" && echo "Patch seems to be already applied" && exit 0 || true
  git -C $MAIN_DIR/vendor/src apply "$PATCH"
fi

$NO_VERBOSE || echo "Create build directory and placing build arguments inside of it, and running gn gen"

mkdir -p $MAIN_DIR/vendor/src/out/Kaleido_${PLATFORM}_${TARGET_ARCH}
cp ..\win_scripts\args_$arch.gn -Destination out\Kaleido_win_$arch\args.gn
# Perform build, result will be out/Kaleido_win/kaleido
gn gen out\Kaleido_win_$arch
