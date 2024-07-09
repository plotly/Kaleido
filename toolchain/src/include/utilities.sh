#!/bin/bash

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  echo "To include utilities.sh, don't execute it- source it"
  exit 1
fi

###
### SETTING BASH MODES ###
###

# It's good to put this at the tope of the script anyway

set -e # exit whole script on any error
set -u # don't allow undefined env var expansion

###
### DEFINING UTILITY FUNCTIONS ###
###

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

# util_export_version will simple export the version variables for use in subshells
util_export_version()
{
  export CHROMIUM_VERSION_TAG
  export DEPOT_TOOLS_COMMIT
}
export -f util_export_version

###
### DETERMING PLATFORM AND OS ###
###

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

###
### FIND THE GIT DIRECTORY ###
###

export MAIN_DIR="$(git rev-parse --show-toplevel)"
$NO_VERBOSE || echo "Found main dir: ${MAIN_DIR}"

if [[ "$MAIN_DIR" == "" ]] || [[ "$MAIN_DIR" == "/" ]]; then
  util_error "git rev-parse returned an empty directory, are we in a git directory?"
fi

mkdir -p "$MAIN_DIR/vendor"


. "$MAIN_DIR"/toolchain/src/include/globals
