#!/bin/bash
set -e
set -u

# Please do your flags first so that utilities uses $NO_VERBOSE, otherwise failure!
usage=(
  "extract_etc is a collection miscellaneous copying into the build directory."
  "Javascript happens in the next script, but this does about everything else."
  "It should be a simple copy/paste script."
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

$NO_VERBOSE || echo "Running 11-extract.sh"

# just making sure to litter these files everywhere at every step
cp "${MAIN_DIR}/src/kaleido/version" "${MAIN_DIR}/src/kaleido/LICENSE.txt" "${MAIN_DIR}/src/kaleido/CREDITS.html" "${BUILD_DIR}" || echo "Missing some meta files, ignoring issue"

mkdir -p "${BUILD_DIR}/etc"
unzip "${MAIN_DIR}/vendor/mathjax/"*.zip -d "${BUILD_DIR}/etc/"
mv "${BUILD_DIR}/etc/Mathjax-"* "${BUILD_DIR}/etc/mathjax/"



# linux copies a bunch of other stuff -- truly not sure how necessary this is
if [[ "$PLATFORM" == "LINUX" ]]; then
  mkdir -p ${BUILD_DIR}/etc/
  cp -r /etc/fonts/ ${BUILD_DIR}/etc/fonts
  mkdir -p ${BUILD_DIR}/xdg
  cp -r /usr/share/fonts/ ${BUILD_DIR}/xdg/
fi
