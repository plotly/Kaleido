#!/bin/bash
set -e
set -u

usage=(
  "build_ninja will run modify and run gn, the last build step before actual chromium build."
  "It appends information about our app to the gn configuration in src/headless."
  "This is currently not version or platform dependent, but it is reasonable it will have to be one day."
  ""
  ""
  "Usage (DO NOT USE --long-flags=something, just --long-flag something):"
  "You can always try -v or --verbose"
  ""

  "Final: this will generate a release build, meaning longer compile, faster startup, perfect timestamp."
  "Updating timestamp will prompt a rebuild of lots of libraries you otherwise don't need to rebuild, so"
  "do this at the end."
  "build_ninja [-f|--final]"

)

FLAGS=("-f" "--final")
ARGFLAGS=()

SCRIPT_DIR=$( cd -- "$( dirname -- $(readlink -f -- "${BASH_SOURCE[0]}") )" &> /dev/null && pwd )
. "$SCRIPT_DIR/include/utilities.sh"

FINAL="$(flags_resolve false "-f" "--final")"
$FINAL && DEV=false || DEV=true

$NO_VERBOSE || echo "Running 06-build_ninja.sh"

$NO_VERBOSE || echo "Release build: $FINAL"
$NO_VERBOSE || echo "Dev build: $DEV"

util_get_version
util_export_version

PATCH="$MAIN_DIR/toolchain/gn_fragments/gn_append.patch"

$NO_VERBOSE || echo "Appending build information to headless/BUILD.gn"
git -C $MAIN_DIR/vendor/src apply --check --reverse "$PATCH" && echo "Patch seems to be already applied" || true
git -C $MAIN_DIR/vendor/src apply "$PATCH" || util_error "Could not apply gn_append.patch, please inspect"

$NO_VERBOSE || echo "Create build directory and placing build arguments inside of it, and running gn gen"

OUTDIR="${MAIN_DIR}/vendor/src/out/Kaleido_${PLATFORM}_${TARGET_ARCH}"
ARGS_FILE="${OUTDIR}/args.gn"
TEMPLATE_FILE="${MAIN_DIR}/toolchain/gn_fragments/gn_args.gn.template"

mkdir -p ${OUTDIR}

SUFFIX="
is_component_build=$DEV
is_official_build=$FINAL
target_cpu=\"${TARGET_ARCH}\""

if [[ ! -f "${ARGS_FILE}" ]] || [[ $(diff $ARGS_FILE <(cat $TEMPLATE_FILE <(echo $SUFFIX))) ]]; then
    cp "${TEMPLATE_FILE}" "${ARGS_FILE}"
    echo "$SUFFIX" >> "${ARGS_FILE}"
fi

$NO_VERBOSE || echo "Args file:"
$NO_VERBOSE || cat ${ARGS_FILE}

( cd $MAIN_DIR/vendor/src && gn gen $OUTDIR )
