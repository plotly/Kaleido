#!/bin/bash
set -e
set -u

usage=(
  "gen_preamble will generate a license file, etc."
  "It copies some stuff into the src/kaleido directory, not sure why."
  "It shouldn't provoke the build system to rebuild anything, we just use copy."
  ""
  "Usage (DO NOT USE --long-flags=something, just --long-flag something):"
  "You can always try -v or --verbose"
)

FLAGS=()
ARGFLAGS=()

SCRIPT_DIR="$( cd -- "$( dirname -- $(readlink -f -- "${BASH_SOURCE[0]}") )" &> /dev/null && pwd )"
. "$SCRIPT_DIR/include/utilities.sh"

$NO_VERBOSE || echo "Running 05-gen_preamble.sh"

util_get_version
util_export_version

# old versions may not work with python3, so do || python
python3 "$MAIN_DIR/vendor/src/tools/licenses/licenses.py" credits > "$MAIN_DIR/CREDITS.html" || python "$MAIN_DIR/vendor/src/tools/licenses/licenses.py" credits > "$MAIN_DIR/CREDITS.html"

cp "$MAIN_DIR/README.md" "$MAIN_DIR/src/kaleido/"
cp "$MAIN_DIR/LICENSE.txt" "$MAIN_DIR/src/kaleido/"
cp "$MAIN_DIR/CREDITS.html" "$MAIN_DIR/src/kaleido/"

