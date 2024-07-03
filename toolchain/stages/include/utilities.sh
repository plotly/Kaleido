#!/bin/bash

set -e # exit on any error

util_error()
{
    echo "Error: $@" >&2
    exit 1
}
export -f util_error

export MAIN_DIR="$(git rev-parse --show-toplevel)" # let's get base directory
export PATH="$MAIN_DIR/repos/depot_tools/bootstrap:$PATH"

if [ "$MAIN_DIR" == "" ] || [ "$MAIN_DIR" == "/" ]; then
  util_error "git rev-parse returned an empty directory, are we in a git directory?"
fi

util_get_version()
{
  if test -f "$MAIN_DIR/.set_version"; then
    . "$MAIN_DIR/.set_version"
  elif [ -z "${DEPO_TOOLS_COMMIT}" ] || [ -z "${CHROMIUM_VERSION_TAG}" ]; then
    util_error "Couldn't find or set env vars for versions, please run set_version."
  fi
}
export -f util_get_version

util_export_version()
{
  export CHROMIUM_VERSION_TAG
  export DEPOT_TOOLS_COMMIT
}
export -f util_export_version
