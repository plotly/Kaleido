#!/bin/bash

echo $PWD
ls
ls /
echo $USER

usage=(
  "set_version will check to see if the chromium/depot_tools version are set- if not,"
  "set_version helps specify the versions. Choose from a list of known combinations"
  "or specify refs exactly for both. Known combinations are in version_configurations."
  "A file will be created in the root of the git directory, .set_version, with the environmental variables."
  "You can also just set flags or environmental variables, and .set_version file will be rewritten."
  ""
  "Usage (DO NOT USE --long-flags=something, just --long-flag something):"
  "You can always try -v or --verbose"
  ""
  "Display this help:"
  "set_version [-h|--h]"
  ""
  "Just get the latest known configuration:"
  "set_version [-l|--latest]"
  ""
  "Specify a known chromium/depot_tools combo (see version_configurations/):"
  "set_version [-c|--chromium] KNOWN_REF"
  ""
  "Specify the refs directly:"
  "set_version [-c|--chromium] REF [-d|--depot] REF"
  ""
  "Force ask:"
  "set_version [-a|--ask]"
)
## PROCESS FLAGS

ASK=false
NO_VERBOSE=true
LATEST=false
while (( $# )); do
  case $1 in
    -h|--help)      printf "%s\n" "${usage[@]}"; exit 0  ;;
    -c|--chromium)  shift; CHROMIUM_VERSION_TAG="$1"     ;;
    -d|--depot)     shift; DEPOT_TOOLS_COMMIT="$1"       ;;
    -v|--verbose)   NO_VERBOSE=false                     ;;
    -l|--latest)    LATEST=true                          ;;
    -a|--ask)       ASK=true                             ;;
    *)              printf "%s\n" "${usage[@]}"; exit 1  ;;
  esac
  shift
done

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd ) # stolen from stack exchange
. "$SCRIPT_DIR/include/utilities.sh"
if $LATEST; then
  $NO_VERBOSE || echo "Getting latest:"
  . "$MAIN_DIR/toolchain/version_configurations/$(ls -v "$MAIN_DIR/toolchain/version_configurations" | tail -1)"
  $NO_VERBOSE || echo "Sourced known configuration:"
  $NO_VERBOSE || echo "Chromium ref: ${CHROMIUM_VERSION_TAG}, depot_tools ref: ${DEPOT_TOOLS_COMMIT}"
elif $ASK; then
  $NO_VERBOSE || echo "--ask forced"
elif [ -n "${CHROMIUM_VERSION_TAG}" ]; then
  $NO_VERBOSE || echo "Found chromium ref: ${CHROMIUM_VERSION_TAG}."
  if [ -n "${DEPOT_TOOLS_COMMIT}" ]; then
    $NO_VERBOSE || echo "Found depo_tools ref: ${DEPO_TOOLS_COMMIT}."
  else
    $NO_VERBOSE || echo "No depo_tools ref found, looking for file w/ that chromium tag."
    if test -f "$MAIN_DIR/toolchain/version_configurations/${CHROMIUM_VERSION_TAG}"; then
      . "$MAIN_DIR/toolchain/version_configurations/${CHROMIUM_VERSION_TAG}"
      $NO_VERBOSE || echo "Sourced known configuration:"
      $NO_VERBOSE || echo "Chromium ref: ${CHROMIUM_VERSION_TAG}, depot_tools ref: ${DEPOT_TOOLS_COMMIT}"
    else
      util_error "Could not find a know configuration for ${CHROMIUM_VERSION_TAG}, see --help"
    fi
  fi
elif test -f "$MAIN_DIR/.set_version"; then
  $NO_VERBOSE || echo "Found a .set_version file."
  . "$MAIN_DIR/.set_version"
  $NO_VERBOSE || echo "Sourced known configuration:"
  $NO_VERBOSE || echo "Chromium ref: ${CHROMIUM_VERSION_TAG}, depot_tools ref: ${DEPOT_TOOLS_COMMIT}"
else
  ASK=true
  $NO_VERBOSE || echo "Don't know what you want, will ask."
fi

if $ASK; then
  PS3="c) Custom"$'\n'"Select a preset version combination (1, 2, etc), or 'c' to specify your own: "
  options=($(ls -v "$MAIN_DIR/toolchain/version_configurations")) # they say not to ever parse ls, oop
  select opt in "${options[@]}"
  do
    if [ "$REPLY" == "c" ] || [ "$REPLY" == "C" ]; then
      read -p "Chromium version tag (or ref): " CHROMIUM_VERSION_TAG
      read -p "Depot tools commit (or ref): " DEPOT_TOOLS_COMMIT
    elif [ "$opt" != "" ]; then
      . "$MAIN_DIR/toolchain/version_configurations/$opt"
      $NO_VERBOSE || echo "Sourced known configuration:"
      $NO_VERBOSE || echo "Chromium ref: ${CHROMIUM_VERSION_TAG}, depot_tools ref: ${DEPOT_TOOLS_COMMIT}."
    else
     util_error "$REPLY not understood"
    fi
    break
  done
fi

echo "CHROMIUM_VERSION_TAG=${CHROMIUM_VERSION_TAG}" > "$MAIN_DIR/.set_version"
echo "DEPOT_TOOLS_COMMIT=${DEPOT_TOOLS_COMMIT}" >> "$MAIN_DIR/.set_version"
$NO_VERBOSE || echo "Wrote .set_version."
util_export_version
