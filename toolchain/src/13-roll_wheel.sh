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

python3 -m pip install setuptools
export KALEIDO_ARCH="$TARGET_ARCH"
pushd "${MAIN_DIR}/src/kaleido/py"
python3 setup.py package
popd

# command, after package

cp "${MAIN_DIR}/src/kaleido/py/dist/"* "${MAIN_DIR}/build/"

# linux called bundle_hash_artifacts
