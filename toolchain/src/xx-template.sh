#!/bin/bash
set -e
set -u

# Please do your flags first so that utilities uses $NO_VERBOSE, otherwise failure!
usage=(
  "xx_template is a template: more description."
  ""
  "Usage (DO NOT USE --long-flags=something, just --long-flag something):"
  "You can always try -v or --verbose"
  ""
  "Display this help:"
  "xx_template [-h|--h]"
  ""
  "Something else you can do"
  "xx_template [-l|--long]"
)

FLAGS=("-l" "--long" "-f" "--full") # add ":" to accept variable arguments after flags
ARGFLAGS=("-t" "--target") # arg flags will take the following word as an argument

SCRIPT_DIR="$( cd -- "$( dirname -- $(readlink -f -- "${BASH_SOURCE[0]}") )" &> /dev/null && pwd )"
. "$SCRIPT_DIR/include/utilities.sh"

LONG="$(flags_resolve false "-l" "--long")" # will resolve true if existing, false if no
FULL="$(flags_resolve false "-f" "--full")"
TARGET="$(flags_resolve ${TARGET-""} -t --target)" # set double-layer default

$NO_VERBOSE || echo "Running xx-template.sh"


util_get_version
util_export_version
