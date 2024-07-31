#!/usr/bin/env bash
set -e
set -u

# Detect if component build is true, and if so, exit TODO

# Please do your flags first so that utilities uses $NO_VERBOSE, otherwise failure!
usage=(
  "extract will attempt to pull all runtime dependencies, including the executable,"
  "out of chromium's build directory into a build/ folder. It compares a chromium zip builder"
  "to a list of what was built what we have and then pulls out what agrees to our build folder."
  "It also pulls out some other stuff."
  ""
  "If you run 10 will clean everything in build put there by later scripts."
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

# build dir is now in include/globals
mkdir -p "$BUILD_DIR"
globals_clean_build_dir

$NO_VERBOSE || echo "We are extracting to $BUILD_DIR"

# mainly reexported, but making sure the python script has it
export MAIN_DIR
export CHROMIUM_VERSION_TAG
export PLATFORM
export TARGET_ARCH
export BUILD_DIR
export SRC_DIR="${MAIN_DIR}/vendor/src/out/Kaleido_${PLATFORM}_${TARGET_ARCH}"
IMPORT='extract = __import__("10-extract_subscript")'

$NO_VERBOSE || echo "MAIN_DIR: $MAIN_DIR"
$NO_VERBOSE || echo "CHROMIUM_V_TAG: $CHROMIUM_VERSION_TAG"
$NO_VERBOSE || echo "PLAT: $PLATFORM"
$NO_VERBOSE || echo "T_ARCH: $TARGET_ARCH"
$NO_VERBOSE || echo "BUILD_DIR: $BUILD_DIR"
$NO_VERBOSE || echo "SRC_DIR: $SRC_DIR"
$NO_VERBOSE || echo "IMPORT LINE: $IMPORT"

CONFIG_DIR="${MAIN_DIR}/toolchain/extract_config/${CHROMIUM_VERSION_TAG}/"
if [ ! -d "${CONFIG_DIR}" ] && $TRY; then
  CONFIG_DIR="${MAIN_DIR}/toolchain/extract_config/$(ls "${MAIN_DIR}/toolchain/extract_config" -vt | head -1)"
elif [ -d "${CONFIG_DIR}" ]; then
  : # optimistic path
else
  util_error "No config dir for $CHROMIUM_VERSION_TAG, look at --try or make your own"
fi
$NO_VERBOSE || echo "Set CONFIG_DIR: $CONFIG_DIR"

if [[ "${PLATFORM}" == "WINDOWS" ]]; then
  CONFIG="$(readlink -m "${CONFIG_DIR}/win-archive-rel.json")"
elif [[ "${PLATFORM}" == "LINUX" ]]; then
  CONFIG="$(readlink -m "${CONFIG_DIR}/linux-archive-rel.json")"
elif [[ "${PLATFORM}" == "OSX" ]]; then
  CONFIG="$(readlink -m "${CONFIG_DIR}/mac-archive-rel.json")"
fi
export CONFIG

if [ ! -f "${CONFIG}-original" ]; then
  util_error "COULDN'T FIND ${CONFIG}-original"
fi
$NO_VERBOSE || echo "Found config: $CONFIG"

$NO_VERBOSE || which python3
if [[ -z "${PYTHON-""}" ]] && which python3 &> /dev/null; then
  PYTHON="python3"
else
  util_error "Couldn't find python3, set in path or set var PYTHON"
fi

export PYTHONPATH="${MAIN_DIR}/toolchain/src/:${PYTHONPATH-""}" 

if $ASSESS; then
  pushd "${MAIN_DIR}/toolchain/src/"
  echo "$($PYTHON -c "$IMPORT; extract.match_json_to_directory('${CONFIG}-original','$SRC_DIR', missing=True, annotate=True, relative=False)")"
  popd
  exit 0
fi
#echo -e "$($PYTHON -c "$IMPORT; extract.hello_world()")"

# may not need to have platform/version branches here if we use different ${CONFIG} each time
if [[ "$PLATFORM" == "LINUX" ]]; then
  $NO_VERBOSE || echo "IN LINUX"
  if [[ "${CHROMIUM_VERSION_TAG}" == "126.0.6478.126" ]] || $TRY; then
    strip -s "${SRC_DIR}/kaleido"
    cp "${SRC_DIR}/kaleido" "${BUILD_DIR}/kaleido"
    chmod +x "${BUILD_DIR}/kaleido"
    FILES=$(echo -e "$($PYTHON -c "$IMPORT; \
extract.match_json_to_directory('\
${CONFIG}-original', \
'$SRC_DIR', \
missing=False, annotate=False, relative=True)")")
    $NO_VERBOSE || echo "Found files: $FILES"
    OLDIFS=$IFS
    IFS=$'\t'
    for f in $FILES; do
      $NO_VERBOSE || echo "Processing file: $f"
      $NO_VERBOSE || echo "SRC_DIR:         ${SRC_DIR}"
      $NO_VERBOSE || echo "BUILD_DIR:       ${BUILD_DIR}"
      $NO_VERBOSE || echo "For creating its directory (2 methods):"
      $NO_VERBOSE || echo '  $(dirname ${BUILD_DIR}/${f}): '"$(readlink -m "$(dirname "${BUILD_DIR}/${f}")")"
      $NO_VERBOSE || echo '  ${BUILD_DIR}$(dirname "$f"):  '"$(readlink -m "${BUILD_DIR}$(dirname "$f")")"
      $NO_VERBOSE || echo "For finding the source:"
      $NO_VERBOSE || echo '  ${SRC_DIR}/${f}:              '"$(readlink -m "${SRC_DIR}/${f}")"
      $NO_VERBOSE || echo '  ${SRC_DIR}${f}:               '"$(readlink -m "${SRC_DIR}${f}")"
      mkdir -p $(dirname "$(readlink -m "${BUILD_DIR}/$f") && cp -r "$(readlink -m "${SRC_DIR}/${f}" "$_" # this might only work on linux :-(
      $NO_VERBOSE || echo
    done
    IFS=$OLDIFS
  fi
  # all linux, copy whole non-kernel lib
  $NO_VERBOSE || echo "Running linux only copies"
  for f in $(sed -nr 's/^.*=> (.*) \(.*/\1/p' <(ldd "${SRC_DIR}/kaleido")); do
    mkdir -p "${BUILD_DIR}/lib/"
    cp "${f}" "${BUILD_DIR}/lib/"
  done
  # manual
  cp /usr/lib/x86_64-linux-gnu/nss/* "${BUILD_DIR}/lib/"
  for f in libdl libpthread librt libm libgcc_s libc; do
    rm "${BUILD_DIR}/lib/${f}"* || echo "No ${f} to remove, moving on..."
  done
  # done
fi

if [[ "$PLATFORM" == "OSX" ]]; then
  $NO_VERBOSE || echo "IN OSX"
  cp "${SRC_DIR}/kaleido" "${BUILD_DIR}/kaleido"
  chmod +x "${BUILD_DIR}/kaleido"
  FILES=$(echo -e "$($PYTHON -c "$IMPORT; \
    extract.match_json_to_directory('\
    ${CONFIG}-original', \
    '$SRC_DIR', \
    missing=False, annotate=False, relative=True)")")
  $NO_VERBOSE || echo "Found files: $FILES"
  OLDIFS=$IFS
  IFS=$'\t'
  for f in $FILES; do
    $NO_VERBOSE || echo "Processing file: $f"
    $NO_VERBOSE || echo "SRC_DIR:         ${SRC_DIR}"
    $NO_VERBOSE || echo "BUILD_DIR:       ${BUILD_DIR}"
    $NO_VERBOSE || echo "For creating its directory (2 methods):"
    $NO_VERBOSE || echo '  $(dirname ${BUILD_DIR}/${f}): '"$(dirname "${BUILD_DIR}/${f}")"
    $NO_VERBOSE || echo '  ${BUILD_DIR}$(dirname "$f"):  '"${BUILD_DIR}$(dirname "$f")"
    $NO_VERBOSE || echo "For finding the source:"
    $NO_VERBOSE || echo '  ${SRC_DIR}/${f}:              '"${SRC_DIR}/${f}"
    $NO_VERBOSE || echo '  ${SRC_DIR}${f}:               '"${SRC_DIR}${f}"
    mkdir -p $(dirname "${BUILD_DIR}/$f") && cp -r "${SRC_DIR}/${f}" "$_" || util_error "OSX doesn't support \$_ maybe"
    $NO_VERBOSE || echo
  done
  IFS=$OLDIFS
  cp "${MAIN_DIR}/vendor/src/out/Kaleido_${PLATFORM}_${TARGET_ARCH}/lib"*.dylib "${BUILD_DIR}/"
fi

if [[ "$PLATFORM" == "WINDOWS" ]]; then
  $NO_VERBOSE || echo "In windows"
  pushd "${MAIN_DIR}/toolchain/src/"
  cp "${SRC_DIR}/kaleido" "${BUILD_DIR}/kaleido"
  chmod +x "${BUILD_DIR}/kaleido"
  FILES=$(echo "$($PYTHON -c "$IMPORT; \
extract.match_json_to_directory('\
${CONFIG}-original', \
'$SRC_DIR', \
missing=False, annotate=False, relative=True)")")
  $NO_VERBOSE || echo "Found files: $FILES"
  OLDIFS=$IFS
  IFS=$'\t'
  for f in $FILES; do
    $NO_VERBOSE || echo "Processing file: $f"
    $NO_VERBOSE || echo "SRC_DIR:         ${SRC_DIR}"
    $NO_VERBOSE || echo "BUILD_DIR:       ${BUILD_DIR}"
    $NO_VERBOSE || echo "For creating its directory (2 methods):"
    $NO_VERBOSE || echo '  $(dirname ${BUILD_DIR}/${f}): '"$(dirname "${BUILD_DIR}/${f}")"
    $NO_VERBOSE || echo '  ${BUILD_DIR}$(dirname "$f"):  '"${BUILD_DIR}$(dirname "$f")"
    $NO_VERBOSE || echo "For finding the source:"
    $NO_VERBOSE || echo '  ${SRC_DIR}/${f}:              '"${SRC_DIR}/${f}"
    $NO_VERBOSE || echo '  ${SRC_DIR}${f}:               '"${SRC_DIR}${f}"
    mkdir -p "${BUILD_DIR}$(dirname "$f")"
    cp -r "${SRC_DIR}${f}" "${BUILD_DIR}$(dirname "$f")"
    $NO_VERBOSE || echo
  done
  IFS=$OLDIFS
  popd
fi
$NO_VERBOSE || echo "Done with platform specific, removing devtools js ui"
rm -rf "${BUILD_DIR}/gen/third_party/devtools-frontend/" # huge and i doubt we need it
