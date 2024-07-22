#!/bin/bash
set -e
set -u


# Please do your flags first so that utilities uses $NO_VERBOSE, otherwise failure!
usage=(
  "roll_wheel runs setup.py and creates the python wheel. You made it!"
  ""
  "Usage (DO NOT USE --long-flags=something, just --long-flag something):"
  "You can always try -v or --verbose"
  ""
  "Display this help:"
  "extract [-h|--h]"
  ""
  ""
)

FLAGS=()
ARGFLAGS=()

SCRIPT_DIR="$( cd -- "$( dirname -- $(readlink -f -- "${BASH_SOURCE[0]}") )" &> /dev/null && pwd )"
. "$SCRIPT_DIR/include/utilities.sh"

util_get_version
util_export_version

$NO_VERBOSE || echo "Running 12-roll_wheel.sh"


# what about ARCH TODO
pushd "${MAIN_DIR}/src/kaleido/py"
python3 setup.py package
popd

# command, after package

rm "${MAIN_DIR}/build/kaleido_${PLATFORM}_${TARGET_ARCH}" || true
zip "${MAIN_DIR}/build/kaleido_${PLATFORM}_${TARGET_ARCH}.zip" "${MAIN_DIR}/build/cc/*"

rm "${MAIN_DIR}/build/kaleido.whl" || true
zip "${MAIN_DIR}/build/kaleido_${PLATFORM}_${TARGET_ARCH}.whl" "${MAIN_DIR}/src/kaleido/py/dist/*"

# linux called bundle_hash_artifacts
