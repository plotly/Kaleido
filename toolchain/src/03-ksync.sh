#!/bin/bash
set -e
set -u

# Please do your flags first so that utilities uses $NO_VERBOSE, otherwise failure!
usage=(
  "ksync will set some env vars and run gclient sync."
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

FLAGS=()
ARGFLAGS=("-c" "--cpus")

SCRIPT_DIR="$( cd -- "$( dirname -- $(readlink -f -- "${BASH_SOURCE[0]}") )" &> /dev/null && pwd )"
. "$SCRIPT_DIR/include/utilities.sh"

CPUS="$(flags_resolve ${CPUS:-1} "-c" "--cpus")"

$NO_VERBOSE || echo "Running 03-ksync.sh"
$NO_VERBOSE || echo "with $CPUS cpus"

util_get_version
util_export_version

export DEPOT_TOOLS_UPDATE=0 # otherwise it advances to the tip of branch main
## but sometimes it skips other necessary things! Thats why we had init_tools
V_FLAG=""
if ! $NO_VERBOSE; then
  ( cd "$MAIN_DIR/vendor/"; gclient sync -D --force --verbose --reset --no-history --jobs=$CPUS --revision="$CHROMIUM_VERSION_TAG" )
else
  ( cd "$MAIN_DIR/vendor/"; gclient sync -D --force --reset --no-history --jobs=$CPUS --revision="$CHROMIUM_VERSION_TAG" )
fi
