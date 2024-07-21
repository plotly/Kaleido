#!/bin/bash
set -e
set -u

# Detect if component build is true, and if so, exit TODO

# Please do your flags first so that utilities uses $NO_VERBOSE, otherwise failure!
usage=(
  "extract will attempt to pull all runtime dependencies, including the executable,"
  "out of chromium's build directory into a build/ folder. It compares a chromium zip builder"
  "to a list of what was built what we have and then pulls out what agrees to our build folder."
  ""
  "Usage (DO NOT USE --long-flags=something, just --long-flag something):"
  "You can always try -v or --verbose"
  ""
  "Display this help:"
  "extract [-h|--h]"
  ""
  "Try: Will use the latest version's patch dir if it can't find its own"
  "extract [-t|--try]"
  ""
  "extract [-s|--assess] will dump its analysis of the situation"
  ""
)

FLAGS=("-t" "--try" "-s" "--assess")
ARGFLAGS=()

SCRIPT_DIR="$( cd -- "$( dirname -- $(readlink -f -- "${BASH_SOURCE[0]}") )" &> /dev/null && pwd )"
. "$SCRIPT_DIR/include/utilities.sh"

util_get_version
util_export_version

$NO_VERBOSE || echo "Running 10-extract.sh"

TRY="$(flags_resolve false "-t" "--try")"
ASSESS="$(flags_resolve false "-s" "--assess")"

BUILD_DIR="${MAIN_DIR}/build/cc/"
if [[ ! -d "$BUILD_DIR" ]]; then
	mkdir -p "$BUILD_DIR"
else
  rm -rf "${MAIN_DIR}/build/cc/*" # rm rf, spell it out to prevent rm -rf accidents
fi

# mainly reexported, but making sure the python script has it
export MAIN_DIR
export CHROMIUM_VERSION_TAG
export PLATFORM
export TARGET_ARCH
export BUILD_DIR
export SRC_DIR="${MAIN_DIR}/vendor/src/out/Kaleido_${PLATFORM}_${TARGET_ARCH}"
IMPORT='extract = __import__("10-extract_subscript")'

CONFIG_DIR="${MAIN_DIR}/toolchain/extract_config/${CHROMIUM_VERSION_TAG}/"
if [ ! -d "${CONFIG_DIR}" ] && $TRY; then
  CONFIG_DIR="${MAIN_DIR}/toolchain/extract_config/$(ls "${MAIN_DIR}/toolchain/extract_config" -vt | head -1)"
elif [ -d "${CONFIG_DIR}" ]; then
  : # optimistic path
else
  util_error "No config dir for $CHROMIUM_VERSION_TAG, look at --try or make your own"
fi

if [[ "$PLATFORM" == "WINDOWS" ]]; then
  CONFIG="$CONFIG_DIR/win-archive-rel.json"
elif [[ "$PLATFORM" == "LINUX" ]]; then
  CONFIG="$CONFIG_DIR/linux-archive-rel.json"
elif [[ "$PLATFORM" == "OSX" ]]; then
  CONFIG="$CONFIG_DIR/mac-archive-rel.json"
fi
export CONFIG

if [[ -z "${PYTHON-""}" ]] && which python3 &> /dev/null; then
  PYTHON="python3"
else
  util_error "Couldn't find python3, set in path or set var PYTHON"
fi

export PYTHONPATH="${MAIN_DIR}/toolchain/src/:${PYTHONPATH-""}" 

if $ASSESS; then
  echo -e "$($PYTHON -c "$IMPORT; extract.match_json_to_directory('${CONFIG}-original','$SRC_DIR', missing=True, annotate=True, relative=False)")"
  exit 0
fi

# echo -e "$($PYTHON -c "$IMPORT; extract.hello_world()")"


if [[ "$PLATFORM" == "LINUX" ]]; then
  if [[ "${CHROMIUM_VERSION_TAG}" == "126.0.6478.126" ]] || $TRY; then
     # fix as to not always put full path there, so we can use it
    cp "${SRC_DIR}/kaleido" "${BUILD_DIR}/kaleido"
    FILES=$(echo -e "$($PYTHON -c "$IMPORT; extract.match_json_to_directory('${CONFIG}-original','$SRC_DIR', missing=False, annotate=False, relative=True)")")
    for f in $FILES; do
      mkdir -p $(dirname "${BUILD_DIR}/$f") && cp -r "${SRC_DIR}/${f}" "$_"
      echo Brrrr: $f
    done
  fi
fi

