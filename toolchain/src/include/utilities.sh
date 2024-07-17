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
util_error()
{
    echo -e "Error: $@" >&2
    exit 1
}

# util_get_version will load the version in .set_version or try to find it in env vars
util_get_version()
{
  if test -f "$MAIN_DIR/.set_version"; then
    . "$MAIN_DIR/.set_version"
  elif [[ -z "${DEPO_TOOLS_COMMIT:-}" ]] || [[ -z "${CHROMIUM_VERSION_TAG:-}" ]]; then
    util_error "Couldn't find or set env vars for versions, please run set_version."
  fi
}

# util_export_version will simple export the version variables for use in subshells
util_export_version()
{
  export CHROMIUM_VERSION_TAG
  export DEPOT_TOOLS_COMMIT
}

###
### FLAGS
###

if [[ -z "${usage-}" ]]; then
  util_error "The script author must create a \`usage\` string-array prior to calling utilities.sh or flags.sh"
fi

if [[ ! "$(declare -p FLAGS)" =~ "declare -a" ]] || [[ ! "$(declare -p ARGFLAGS)" =~ "declare -a" ]]; then
  util_error "The script author must at least declare a FLAGS and ARGFLAGS array. FLAGS=(); ARGFLAGS=();"
fi

declare -A ARGS
NO_VERBOSE=true
while (( $# )); do
  case $1 in
    -h|--help)      printf "%s\n" "${usage[@]}"; exit 0  ;;
    -v|--verbose)   NO_VERBOSE=false                     ;;
    *)
      if [[ "${1}" == -* ]]; then
        if [[ " ${FLAGS[*]} " =~ " ${1} " ]]; then
          ARGS["${1}"]=true
        elif [[ " ${ARGFLAGS[*]} " =~ " ${1} " ]]; then
          KEY="${1}"; shift
          ARGS["$KEY"]="${1}"
        elif [[ "${1}" == "--" ]]; then
          shift
          ARGS[":"]="${@}"
          break 1
        else
          util_error "Unknown flag: \"${1}\". See --help."
        fi
      elif [[ " ${FLAGS[*]} " =~ " : " ]]; then
        ARGS[":"]="${@}"
        break 1
      else
        util_error "Unknown argument: ${1}. See --help" || true
      fi
      ;;
  esac
  shift
done

# flags_resolve checks several keys and returns the first one that has a value
flags_resolve()
{
  DEFAULT="$1"
  shift
  while (( $# )); do
    [[ -v ARGS["$1"] ]] && echo "${ARGS[$1]}" && return || true
    shift
  done
  echo "$DEFAULT"
}

$NO_VERBOSE || printf "Flags:\n%s\n" "${!array[@]}" "${array[@]}" | pr -2t

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

###
### FIND THE GIT DIRECTORY ###
###

export MAIN_DIR="${MAIN_DIR-$(git rev-parse --show-toplevel)}"
$NO_VERBOSE || echo "Found main dir: ${MAIN_DIR}"

if [[ "$MAIN_DIR" == "" ]] || [[ "$MAIN_DIR" == "/" ]]; then
  util_error "git rev-parse returned an empty directory, are we in a git directory?"
fi

mkdir -p "$MAIN_DIR/vendor"


. "$MAIN_DIR"/toolchain/src/include/globals
