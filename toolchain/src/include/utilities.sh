#!/bin/bash

# exit whole script on any error
set -e

# don't allow undefined env var expansion
set -u

# util_error will take a string as an argument and print it to error, and quit
util_error() # print error and quit
{
    echo "Error: $@" >&2
    exit 1
}
export -f util_error

# util_get_version will load the version in .set_version or try to find it in env vars
util_get_version()
{
  if test -f "$MAIN_DIR/.set_version"; then
    . "$MAIN_DIR/.set_version"
  elif [[ -z "${DEPO_TOOLS_COMMIT:-}" ]] || [[ -z "${CHROMIUM_VERSION_TAG:-}" ]]; then
    util_error "Couldn't find or set env vars for versions, please run set_version."
  fi
}
export -f util_get_version

# util will simple export the version variables for use in subshells
util_export_version()
{
  export CHROMIUM_VERSION_TAG
  export DEPOT_TOOLS_COMMIT
}
export -f util_export_version

# The following code tries to determine what operating system we're running
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

# The following code tries to determine what architecture we're running
HOST_ARCH=$(uname -m)
if [[ "$HOST_ARCH" == x86_64* ]]; then
  HOST_ARCH="x64"
elif [[ "$HOST_ARCH" == i*86 ]]; then
  HOST_ARCH="x32"
elif  [[ "$HOST_ARCH" == arm* ]]; then
  HOST_ARCH="arm"
fi

if ! [[ "$HOST_ARCH" =~ ^(x64|x32|arm)$ ]]; then
  util_error "$HOST_ARCH is not a supported architecture for building."
fi
$NO_VERBOSE || echo "Found architecture: $HOST_ARCH"

# Lets find our top level directory
export MAIN_DIR="$(git rev-parse --show-toplevel)"
$NO_VERBOSE || echo "Found main dir: ${MAIN_DIR}"

if [[ "$MAIN_DIR" == "" ]] || [[ "$MAIN_DIR" == "/" ]]; then
  util_error "git rev-parse returned an empty directory, are we in a git directory?"
fi

# This will add depot_tools to our path,
# It would make sense to put this elsewhere but we need it in every script
if [[ "$PLATFORM" == "WINDOWS" ]]; then
  export PATH="$MAIN_DIR/repos/depot_tools/bootstrap:$PATH" # TODO TODO WE MAY NOT WANT THIS IN NON-WINDOWS
  $NO_VERBOSE || echo "Modified path to add future depot_tools/bootstrap/ directory"
elif [[ "$PLATFORM" == "LINUX" ]]; then
  export PATH="$MAIN_DIR/repos/depot_tools/:$PATH"
  $NO_VERBOSE || echo "Modified path to add future depot_tools/ directory"
elif [[ "$PLATFORM" == "OSX" ]]; then
  export PATH="$MAIN_DIR/repos/depot_tools/:$PATH"
  $NO_VERBOSE || echo "Modified path to add future depot_tools/ directory"
fi
