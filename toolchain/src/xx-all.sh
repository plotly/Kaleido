#!/bin/bash
set -e
set -u

# Please do your flags first so that utilities uses $NO_VERBOSE, otherwise failure!
usage=(
  "all is a shortcut to running the scripts. If the first argument is a number, -0:, -1:, -2:, it will run that stage."
  "Anything besides that or after that will be passed to the command or every command run."
  ""
  "Usage (DO NOT USE --long-flags=something, just --long-flag something):"
  "You can always try -v or --verbose"
  ""
  "Display this help:"
  "all [-h|--h]"
  ""
  "Example: You can specify a specific stage and its flags. The following are equivalent:"
  "all -0: --latest"
  "set_version --latest"
  ""
  "Or, you can skip the number and everything will be passed to every command."
  "So, it really only works with --verbose."
  ""
  "-0: set_version"
  "-1: fetch_tools"
  "-2: init_tools"
  "-3:"
  "-4:"
  "-5:"
  "-6:"
  "-7:"
  "-8:"
)

FLAGS=(":" "-0:" "-1:" "-2:" "-3:" "-4:" "-5:" "-6:" "-7:", "-8:")
ARGFLAGS=("")

SCRIPT_DIR=$( cd -- "$( dirname -- $(readlink -f -- "${BASH_SOURCE[0]}") )" &> /dev/null && pwd )
. "$SCRIPT_DIR/include/utilities.sh"

ZERO=$(flags_resolve false "-0:")
ONE=$(flags_resolve false "-1:")
TWO=$(flags_resolve false "-2:")
THREE=$(flags_resolve false "-3:")
FOUR=$(flags_resolve false "-4:")
FIVE=$(flags_resolve false "-5:")
SIX=$(flags_resolve false "-6:")
SEVEN=$(flags_resolve false "-7:")
EIGHT=$(flags_resolve false "-8:")

NOT_ALL=$ONE || $TWO || $THREE || $FOUR || $FIVE || $SIX || $SEVEN || $EIGHT || false
ALL=false
if $NOT_ALL: ALL=true
$NO_VERBOSE || echo "Running xx-all.sh"

# check for something in path before running
if [[ $ZERO ]] || [[ $ALL ]]; then
  if $(which set_version &>/dev/null); then
    set_version $(flags_resolve "" ":")
  else
    $SCRIPT_DIR/00-set_version.sh $(flags_resolve "" ":")
  fi
fi
if [[ $ONE ]] || [[ $ALL ]]; then
  if $(which fetch_tools &>/dev/null); then
    fetch_tools $(flags_resolve "" ":")
  else
    $SCRIPT_DIR/01-fetch_tools.sh $(flags_resolve "" ":")
  fi
fi
if [[ $TWO ]] || [[ $ALL ]]; then
  if $(which init_tools &>/dev/null); then
    fetch_tools $(flags_resolve "" ":")
  else
    $SCRIPT_DIR/02-init_tools.sh $(flags_resolve "" ":")
  fi
fi

if [[ $THREE ]] || [[ $ALL ]]; then
  :
fi

if [[ $FOUR ]] || [[ $ALL ]]; then
  :
fi

if [[ $FIVE ]] || [[ $ALL ]]; then
  :
fi

if [[ $SIX ]] || [[ $ALL ]]; then
  :
fi

if [[ $SEVEN ]] || [[ $ALL ]]; then
  :
fi

if [[ $EIGHT ]] || [[ $ALL ]]; then
  :
fi
