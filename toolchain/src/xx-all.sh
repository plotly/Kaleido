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
  "all -0 -- --latest"
  "set_version --latest"
  ""
  "Or, you can skip the number and everything will be passed to every command."
  "So, it really only works with --verbose."
  ""
  "-0  set_version      - just sets some env vars for versions"
  "-1  fetch_tools      - clones depot_tools"
  "-2  init_tools       - runs whatever depot_tools downloads it wants"
  "-3  ksync            - downloads chromium"
  "-4  patch_chromium   - patches chromium w/ our patches"
  "-5  gen_preamble     - copies readme, licenses, etc"
  "-6  build_ninja      - prepares gn and runs gn gen to build ninja"
  "-7  write_kversion   - writes a version text file for kaleido"
  "-8  sync_cpp         - will sync kaleido c++ do chromium src"
  "-9  build_kaleido    - builds kaleido's c++"
  "-10 extract          - attempts to extract our build from chromium src folder"
  "-11 extract_etc      - moves extraneous, extra, and vendor deps into the build folder"
  "-12 build_js         - uses npm to build js and move to build folder"
  "-13 roll_wheel       - build python wheel"
)

FLAGS=(":" "-0" "-1" "-2" "-3" "-4" "-5" "-6" "-7" "-8" "-9" "-10" "-11" "-12" "-13")
ARGFLAGS=("")

SCRIPT_DIR="$( cd -- "$( dirname -- $(readlink -f -- "${BASH_SOURCE[0]}") )" &> /dev/null && pwd )"
. "$SCRIPT_DIR/include/utilities.sh"

ZERO=$(flags_resolve false "-0")
ONE=$(flags_resolve false "-1")
TWO=$(flags_resolve false "-2")
THREE=$(flags_resolve false "-3")
FOUR=$(flags_resolve false "-4")
FIVE=$(flags_resolve false "-5")
SIX=$(flags_resolve false "-6")
SEVEN=$(flags_resolve false "-7")
EIGHT=$(flags_resolve false "-8")
NINE=$(flags_resolve false "-9")
TEN=$(flags_resolve false "-10")
ELEVEN=$(flags_resolve false "-11")
TWELVE=$(flags_resolve false "-12")
THIRTEEN=$(flags_resolve false "-13")

ALL=true
if $ZERO || $ONE || $TWO || $THREE || $FOUR || $FIVE || $SIX || $SEVEN || $EIGHT || $NINE || $TEN || $ELEVEN || $TWELVE || $THIRTEEN; then
  $NO_VERBOSE || echo "Turning off ALL"
  ALL=false
fi

$NO_VERBOSE || echo "Running xx-all.sh"
$NO_VERBOSE || echo "Running all? $ALL"

# check for something in path before running
if $ZERO || $ALL; then
  $NO_VERBOSE || echo "Running 0"
  if $(which set_version &>/dev/null); then
    set_version $(flags_resolve "" ":")
  else
    $SCRIPT_DIR/00-set_version.sh $(flags_resolve "" ":")
  fi
fi

if $ONE || $ALL; then
  $NO_VERBOSE || echo "Running 1"
  if $(which fetch_tools &>/dev/null); then
    fetch_tools $(flags_resolve "" ":")
  else
    $SCRIPT_DIR/01-fetch_tools.sh $(flags_resolve "" ":")
  fi
fi

if $TWO || $ALL; then
  $NO_VERBOSE || echo "Running 2"
  if $(which init_tools &> /dev/null); then
    init_tools $(flags_resolve "" ":")
  else
    $SCRIPT_DIR/02-init_tools.sh $(flags_resolve "" ":")
  fi
fi

if $THREE || $ALL; then
  $NO_VERBOSE || echo "Running 3"
  if $(which ksync &> /dev/null); then
    ksync $(flags_resolve "" ":")
  else
    $SCRIPT_DIR/03-ksync.sh $(flags_resolve "" ":")
  fi
fi

if $FOUR || $ALL; then
  $NO_VERBOSE || echo "Running 4"
  if $(which patch_chromium &> /dev/null); then
    patch_chromium $(flags_resolve "" ":")
  else
    $SCRIPT_DIR/04-patch_chromium.sh $(flags_resolve "" ":")
  fi
fi

if $FIVE || $ALL; then
  $NO_VERBOSE || echo "Running 5"
  if $(which gen_preamble &> /dev/null); then
    gen_preamble $(flags_resolve "" ":")
  else
    $SCRIPT_DIR/05-gen_preamble.sh $(flags_resolve "" ":")
  fi
fi

if $SIX || $ALL; then
  $NO_VERBOSE || echo "Running 6"
  if $(which build_ninja &> /dev/null); then
    build_ninja $(flags_resolve "" ":")
  else
    $SCRIPT_DIR/06-build_ninja.sh $(flags_resolve "" ":")
  fi
fi

if $SEVEN || $ALL; then
  $NO_VERBOSE || echo "Running 7"
  if $(which write_kversion &> /dev/null); then
    write_kversion $(flags_resolve "" ":")
  else
    $SCRIPT_DIR/07-write_kversion.sh $(flags_resolve "" ":")
  fi
fi

if $EIGHT || $ALL; then
  $NO_VERBOSE || echo "Running 8"
  if $(which sync_cpp &> /dev/null); then
    sync_cpp $(flags_resolve "" ":")
  else
    $SCRIPT_DIR/08-sync_cpp.sh $(flags_resolve "" ":")
  fi
fi

if $NINE || $ALL; then
  $NO_VERBOSE || echo "Running 9"
  if $(which build_kaleido &> /dev/null); then
    build_kaleido $(flags_resolve "" ":")
  else
    $SCRIPT_DIR/09-build_kaleido.sh $(flags_resolve "" ":")
  fi
fi

if $TEN || $ALL; then
  $NO_VERBOSE || echo "Running 10"
  if $(which extract &> /dev/null); then
    extract $(flags_resolve "" ":")
  else
    $SCRIPT_DIR/10-extract.sh $(flags_resolve "" ":")
  fi
fi

if $ELEVEN || $ALL; then
  $NO_VERBOSE || echo "Running 11"
  if $(which extract_etc &> /dev/null); then
    extract_etc $(flags_resolve "" ":")
  else
    $SCRIPT_DIR/11-extract_etc.sh $(flags_resolve "" ":")
  fi
fi

if $TWELVE || $ALL; then
  $NO_VERBOSE || echo "Running 12"
  if $(which build_js &> /dev/null); then
    build_js $(flags_resolve "" ":")
  else
    $SCRIPT_DIR/12-build_js.sh $(flags_resolve "" ":")
  fi
fi

if $THIRTEEN || $ALL; then
  $NO_VERBOSE || echo "Running 13"
  if $(which roll_wheel &> /dev/null); then
    roll_wheel $(flags_resolve "" ":")
  else
    $SCRIPT_DIR/13-roll_wheel.sh $(flags_resolve "" ":")
  fi
fi
