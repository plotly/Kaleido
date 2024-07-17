#!/bin/bash
set -e
set -u

usage=(
  "build_kaleido does the c++ build."
  ""
  ""
  "Usage (DO NOT USE --long-flags=something, just --long-flag something):"
  "You can always try -v or --verbose"
  ""
  "Set number of cpus:"
  "build_kaleido [-c|--cpus] CPUS"
)

FLAGS=()
ARGFLAGS=()

SCRIPT_DIR="$( cd -- "$( dirname -- $(readlink -f -- "${BASH_SOURCE[0]}") )" &> /dev/null && pwd )"
. "$SCRIPT_DIR/include/utilities.sh"

ARGFLAGS=("-c" "--cpus")

$NO_VERBOSE || echo "Running 09-build_kaleido.sh"

CPUS="$(flags_resolve ${CPUS:-1} "-c" "--cpus")"

util_get_version
util_export_version

OUTDIR="${MAIN_DIR}/vendor/src/out/Kaleido_${PLATFORM}_${TARGET_ARCH}"

( cd "${MAIN_DIR}/vendor/src"; ninja -C $OUTDIR -j $CPUS kaleido )
