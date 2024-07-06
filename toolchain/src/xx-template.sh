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
## PROCESS FLAGS

NO_VERBOSE=true
while (( $# )); do
  case $1 in
    -h|--help)        printf "%s\n" "${usage[@]}"; exit 0  ;;
    -v|--verbose)     NO_VERBOSE=false                     ;;
    *)                printf "%s\n" "${usage[@]}"; exit 1  ;;
  esac
  shift
done

$NO_VERBOSE || echo "Running xx-template.sh"

SCRIPT_DIR=$( cd -- "$( dirname -- $(readlink -f -- "${BASH_SOURCE[0]}") )" &> /dev/null && pwd )
. "$SCRIPT_DIR/include/utilities.sh"

util_get_version
util_export_version
