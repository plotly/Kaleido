#!/bin/bash
set -e
set -u

# Detect if component build is true, and if so, exit TODO

# Please do your flags first so that utilities uses $NO_VERBOSE, otherwise failure!
usage=(
  "build_js will run npm build commands in the js src repo and copy the build artifacts"
  "into our build directory."
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

$NO_VERBOSE || echo "Running 10-extract.sh"

export BUILD_DIR="${MAIN_DIR}/build/js/"
if [[ ! -d "$BUILD_DIR" ]]; then
	mkdir -p "$BUILD_DIR"
else
  rm -rf "${MAIN_DIR}/build/js/*" # rm rf, spell it out to prevent rm -rf accidents
fi

export SRC_DIR="${MAIN_DIR}/src/kaleido/js/"

pushd "${SRC_DIR}"
mkdir -p build/
npm install
npm run clean
npm run build
popd

cp -r "${SRC_DIR}/build/*" "${BUILD_DIR}"
