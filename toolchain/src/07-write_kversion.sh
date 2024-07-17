#!/bin/bash
set -e
set -u

usage=(
  "write_kversion creates at text file that lists the kaleido version"
  "It is not listed as a dependency so it should not provoke a rebuild."
  "However, it is a runtime dependency and kaleido will crash without it."
  ""
  ""
  "Usage (DO NOT USE --long-flags=something, just --long-flag something):"
  "You can always try -v or --verbose"
  ""
)

FLAGS=()
ARGFLAGS=()

SCRIPT_DIR="$( cd -- "$( dirname -- $(readlink -f -- "${BASH_SOURCE[0]}") )" &> /dev/null && pwd )"
. "$SCRIPT_DIR/include/utilities.sh"

$NO_VERBOSE || echo "Running 07-write_kversion"

util_get_version
util_export_version

version="$(python3 "${MAIN_DIR}/toolchain/build_pep440_version.py")"
$NO_VERBOSE || echo "Version: $version"
echo -n "$version" > "${MAIN_DIR}/src/kaleido/version"
