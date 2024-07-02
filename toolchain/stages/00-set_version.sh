#!/bin/bash

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd ) # stolen from stack exchange
. $SCRIPT_DIR/include/utilities.sh

usage=(
  "set_version will check to see if the chromium/depot_tools version are set- if not,"
  "set_version helps specify the versions. Choose from a list of known combinations"
  "or specify refs exactly for both. Known combinations are in version_configurations."
  "A file will be created in the root of the git directory, .set_version, with the environmental variables."
  "You can also just set flags or environmental variables, and .set_version file will be rewritten."
  ""
  "Usage (DO NOT USE --long-flags=something, just --long-flag something):"
  ""
  "Display this help:"
  "set_version [-h|--h]"
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

print_usage() {
  printf "Usage: ..."
}

ASK=false
while (( $# )); do
  case $1 in
    -h|--help)      printf "%s\n" "${usage[@]}"; exit 0  ;;
    -c|--chromium)  shift; CHROMIUM_VERSION_TAG="$1"     ;;
    -d|--depot)     shift; DEPOT_TOOLS_COMMIT="$1"       ;;
    -a|--ask)       ASK=true
    *)              printf "%s\n" "${usage[@]}"; exit 1  ;;
  esac
  shift
done

if $ASK; then
  :
elif [ -n "${CHROMIUM_VERSION_TAG}" ]; then
  if [ -n "${DEPOT_TOOLS_COMMIT}" ]; then
    :
  else:
    if test -f $MAIN_DIR/toolchain/version_configurations/${CHROMIUM_VERSION_TAG}: then
      . $MAIN_DIR/toolchain/version_configurations/${CHROMIUM_VERSION_TAG}
    else:
      error "Could not find a know configuration for ${CHROMIUM_VERSION_TAG}, see --help"
    fi
elif test -f $MAIN_DIR/.set_version: then
  . $MAIN_DIR/.set_version
else:
  ASK=true
fi

if $ASK; then
  PS3="c) Custom"$'\n'"Select a preset version combination (1, 2, etc), or 'c' to specify your own: "
  options=($(ls -v $MAIN_DIR/toolchain/version_configurations)) # they say not to ever parse ls, oop
  select opt in "${options[@]}"
  do
        echo "$REPLY, $opt"
        if [ "$REPLY" == "c" ] or [ "$REPLY" == "C" ]; then
          read -p "Chromium version tag (or ref): " CHROMIUM_VERSION_TAG
          read -p "Depot tools commit (or ref): " DEPOT_TOOLS_COMMIT
        elif [ "$opt" == "" ]; then
          . $MAIN_DIR/toolchain/version_configurations/$opt
        else
         error "$REPLY not understood"
        fi
        break
  done
fi

echo "CHROMIUM_VERSION_TAG=${CHROMIUM_VERSION_TAG}" > $MAIN_DIR/.set_version
echo "DEPOT_TOOLS_COMMIT=${DEPOT_TOOLS_COMMIT}" >> $MAIN_DIR/.set_version

export CHROMIUM_VERSION_TAG
export DEPOT_TOOLS_COMMIT
