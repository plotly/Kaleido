#!/bin/bash
set -e
set -u

# Please do your flags first so that utilities uses $NO_VERBOSE, otherwise failure!
usage=(
  "ksync will set some env vars and run gclient sync in an OS dependent manner"
  ""
  "Usage (DO NOT USE --long-flags=something, just --long-flag something):"
  "You can always try -v or --verbose"
  ""
  "Display this help:"
  "ksync [-h|--h]"
  ""
  "Set number of cpus:"
  "ksync [-c|--cpus] CPUS"
  ""
  ""
)
## PROCESS FLAGS

FLAGS=()
ARGFLAGS=("-c" "--cpus")

SCRIPT_DIR=$( cd -- "$( dirname -- $(readlink -f -- "${BASH_SOURCE[0]}") )" &> /dev/null && pwd )
. "$SCRIPT_DIR/include/utilities.sh"

CPUS="$(flags_resolve ${CPUS:-1} "-c" "--cpus")"

$NO_VERBOSE || echo "Running 03-ksync.sh"
$NO_VERBOSE || echo "with $CPUS cpus"

util_get_version
util_export_version

export DEPOT_TOOLS_UPDATE=0 # otherwise it advances to the tip of branch main
## but sometimes it does other necessary things!


# This may change with depot tools vesion, and it still needs to be worked out per platform
if [[ "$PLATFORM" == "WINDOWS" ]]; then
  $NO_VERBOSE || echo "TODO" # TODO (look at your comment in fetch_chromium)
elif [[ "$PLATFORM" == "LINUX" ]]; then
  ( cd $MAIN_DIR/vendor/; gclient sync -D --force --reset --no-history --jobs=$CPUS --revision=$CHROMIUM_VERSION_TAG )
elif [[ "$PLATFORM" == "OSX" ]]; then
  $NO_VERBOSE || echo "Did nothing for OSX, we will have to do something, probably the same as linux." # TODO
fi
