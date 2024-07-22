#!/bin/bash
set -e
set -u


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

$NO_VERBOSE || echo "Running 12-build_js.sh"

export SRC_DIR="${MAIN_DIR}/src/kaleido/js/"

pushd "${SRC_DIR}"
mkdir -p build/
npm install
npm run clean
npm run build
popd

mkdir "${BUILD_DIR}/js/"
cp -r "${SRC_DIR}/build/"*.js "${BUILD_DIR}/js/"
