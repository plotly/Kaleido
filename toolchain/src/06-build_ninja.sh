#!/bin/bash
set -e
set -u

usage=(
  "build_ninja will run modify and run gn, the last build step before actual chromium build."
  "It appends information about our app to the gn configuration in src/headless."
  "This is currently not version or platform dependent, but it is reasonable it will have to be one day."
  "It is important to understand that we cannabilize the headless/app example in order to absorb its boilerplate."
  "This script will modify the headless directory's build configurations (see gn_fragments in toolchain),"
  "mainly for renaming and reducing unecessary dependencies, and sync_cpp will replace the example app with kaleido."
  ""
  ""
  "Usage (DO NOT USE --long-flags=something, just --long-flag something):"
  "You can always try -v or --verbose"
  ""

  "Final: this will generate a release build, meaning longer compile, faster startup, perfect timestamp."
  "Updating timestamp will prompt a rebuild of lots of libraries you otherwise don't need to rebuild, so"
  "do this at the end."
  "build_ninja [-f|--final]"
  ""
  "Show: show will just let you know if you last did a development build or not"
  "build_ninja [-s|--show]"
  ""
  "List: list is a shortcut for gn args --list, which must be run after running build_ninja once and will show"
  "will show you all possible arguments."
  "build_ninja [-l|--list]"
  ""
  "Try: Will use the latest version's patch dir if it can't find its own"
  "build_ninja [-t|--try]"
  ""
)

# todo args --list
# todo show
FLAGS=("-f" "--final" "-s" "--show" "-l" "--list" "-t" "--try")
ARGFLAGS=()

SCRIPT_DIR="$( cd -- "$( dirname -- $(readlink -f -- "${BASH_SOURCE[0]}") )" &> /dev/null && pwd )"
. "$SCRIPT_DIR/include/utilities.sh"

FINAL="$(flags_resolve false "-f" "--final")"
$FINAL && DEV=false || DEV=true

SHOW="$(flags_resolve false "-s" "--show")"
LIST="$(flags_resolve false "-l" "--list")"



$NO_VERBOSE || echo "Running 06-build_ninja.sh"

$NO_VERBOSE || echo "Release build: $FINAL"
$NO_VERBOSE || echo "Dev build: $DEV"

TRY="$(flags_resolve false "-t" "--try")"

util_get_version
util_export_version

GN_FRAG_DIR="${MAIN_DIR}/toolchain/gn_fragments/$CHROMIUM_VERSION_TAG"
if [ ! -d "$GN_FRAG_DIR" ] && $TRY; then
  GN_FRAG_DIR="${MAIN_DIR}/toolchain/gn_fragments/$(ls "${MAIN_DIR}/src/vendor-patches/chromium" -vt | head -1)"
elif [ -d "$GN_FRAG_DIR" ]; then
  : # optimistic path
else
  util_error "No gn_fragment dir for $CHROMIUM_VERSION_TAG, look at --try or make your own"
fi

BUILD_SUFFIX="${GN_FRAG_DIR}/BUILD.gn"
TARGET="${MAIN_DIR}/vendor/src/headless/BUILD.gn"
OUTDIR="${MAIN_DIR}/vendor/src/out/Kaleido_${PLATFORM}_${TARGET_ARCH}"
ARGS_FILE="${OUTDIR}/args.gn"
TEMPLATE_FILE="${GN_FRAG_DIR}/args.gn"

if $SHOW; then
  if [[ -f "${ARGS_FILE}" ]]; then
    cat "${ARGS_FILE}"
  else
    echo "Script never run, nothing to show"
  fi
  exit 0
fi

if $LIST; then
  if [[ -f "${ARGS_FILE}" ]]; then
    ( cd "$MAIN_DIR/vendor/src" && gn args --list "$OUTDIR" )
  else
    echo "You haven't run the main script yet, that needs to happen once before this will work"
  fi
  exit 0
fi

LINE_NO=$(grep "$TARGET" -ne "$(head -n 1 "$BUILD_SUFFIX")" | cut -f1 -d:)
$NO_VERBOSE || echo "$(head -n 1 "$BUILD_SUFFIX")"
$NO_VERBOSE || echo "$LINE_NO"
if [[ -n "$LINE_NO" ]]; then
  head "$TARGET" -n $(($LINE_NO - 1)) > "${TARGET}.TEMP"
  mv "${TARGET}.TEMP" "$TARGET"
fi
$NO_VERBOSE || echo "Appending build information to headless/BUILD.gn"
cat "$BUILD_SUFFIX" >> "$TARGET"

$NO_VERBOSE || cat "$TARGET"

$NO_VERBOSE || echo "Create build directory and placing build arguments inside of it, and running gn gen"


mkdir -p "${OUTDIR}"

# note- this will make timestamp not accurate for chromium, but best choice rn, see build/compute_build_timestamp.py
SUFFIX="
is_component_build=$DEV
is_official_build=false
target_cpu=\"${TARGET_ARCH}\""

if [[ ! -f "${ARGS_FILE}" ]] || [[ $(diff "$ARGS_FILE" <(cat "$TEMPLATE_FILE" <(echo "$SUFFIX"))) ]]; then
    cp "${TEMPLATE_FILE}" "${ARGS_FILE}"
    echo "$SUFFIX" >> "${ARGS_FILE}"
fi

$NO_VERBOSE || echo "Args file:"
$NO_VERBOSE || cat "${ARGS_FILE}"

( cd "$MAIN_DIR/vendor/src" && gn gen "$OUTDIR" )
