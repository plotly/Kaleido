#!/bin/bash

set -e # exit on any error

util_error()
{
    echo "Error: $@" >&2
    exit 1
}
export -f util_error

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

PLATFORM=""
case "$OSTYPE" in
  solaris*) PLATFORM="SOLARIS" ;;
  darwin*)  PLATFORM="OSX" ;;
  linux*)   PLATFORM="LINUX" ;;
  bsd*)     PLATFORM="BSD" ;;
  msys*)    PLATFORM="WINDOWS" ;;
  cygwin*)  PLATFORM="WRONG_WINDOWS" ;; # our scripts should always return msys
  *)        PLATFORM="$OSTYPE" ;;
esac

if ! [[ "$PLATFORM" =~ ^(OSX|LINUX|WINDOWS)$ ]]; then
  util_error "$PLATFORM is not a supported platform for building."
fi
$NO_VERBOSE || echo "Found platform: $PLATFORM"


ARCH=$(uname -m)
if [[ "$ARCH" == x86_64* ]]; then
  ARCH="x64"
elif [[ "$ARCH" == i*86 ]]; then
  ARCH="x32"
elif  [[ "$ARCH" == arm* ]]; then
  ARCH="arm"
fi

if ! [[ "$ARCH" =~ ^(x64|x32|arm)$ ]]; then
  util_error "$ARCH is not a supported architecture for building."
fi
$NO_VERBOSE || echo "Found architecture: $ARCH"

export MAIN_DIR="$(git rev-parse --show-toplevel)" # let's get base directory
$NO_VERBOSE || echo "Found main dir: ${MAIN_DIR}"

if [ "$PLATFORM" == "WINDOWS" ]; then
  export PATH="$MAIN_DIR/repos/depot_tools/bootstrap:$PATH" # TODO TODO WE MAY NOT WANT THIS IN NON-WINDOWS
  $NO_VERBOSE || echo "Modified path to add future boostrap directory"
else
  util_error "Non-windows not supported yet"
fi

