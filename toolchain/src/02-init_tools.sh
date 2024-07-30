#!/bin/bash
set -e
set -u

# Please do your flags first so that utilities uses $NO_VERBOSE, otherwise failure!
usage=(
  "init_tools will run some some commands that google recommends or requires before other build steps."
  "It can be version and platform dependent."
  ""
  "Usage (DO NOT USE --long-flags=something, just --long-flag something):"
  "You can always try -v or --verbose"
  ""
  "Display this help:"
  "init_tools [-h|--h]"
  ""
  "Dry run: just show me the scripts that would be run, don't run them."
  "init_tools [-d|--dry-run]"
  ""
  ""
  "Try: if it can find a matching version to the one select, use the latest"
  "init_tools [-t|--try]"
)
## PROCESS FLAGS

FLAGS=("-d" "--dry-run" "-t" "--try")
ARGFLAGS=()

SCRIPT_DIR="$( cd -- "$( dirname -- $(readlink -f -- "${BASH_SOURCE[0]}") )" &> /dev/null && pwd )"
. "$SCRIPT_DIR/include/utilities.sh"

SHOW="$(flags_resolve false "-d" "--dry-run")"
TRY="$(flags_resolve false "-t" "--try")"

$NO_VERBOSE || echo "Running 02-init_tools.sh"

util_get_version
util_export_version

# This may change with depot tools vesion, and it still needs to be worked out per platform
if [[ "$PLATFORM" == "WINDOWS" ]]; then
  if [[ "$CHROMIUM_VERSION_TAG" == "88.0.4324.150" ]]; then
    util_error "no worky"
    cmd.exe /c cipd_bin_setup.bat
    cmd.exe /c 'bootstrap\win_tools.bat'
  elif [[ "$CHROMIUM_VERSION_TAG" == "126.0.6478.126" ]] || $TRY; then
    pushd "$MAIN_DIR/vendor/depot_tools/"
    COMMAND="
set DEPOT_TOOLS_UPDATE=0\n
set DEPOT_TOOLS_WIN_TOOLCHAIN=0\n
set PATH=$MAIN_DIR\\\vendor\\\depot_tools\\\;$MAIN_DIR\\\vendor\\\depot_tools\\\bootstrap;%PATH%\n
set CPUS=$CPUS\n
where python3\n
cipd_bin_setup.bat\n
bootstrap\\\win_tools.bat\n
exit"
    echo -e "$COMMAND" | cmd
    popd
  else
    util_error "No elif branch in 02-init_tools.sh for this version $CHROMIUM_VERSION_TAG, as of today, you still have to add the branch manually. You can add an elif statement right where you find this error, so search for it. (or see help)"
  fi
elif [[ "$PLATFORM" == "LINUX" ]]; then
  mkdir -p "$MAIN_DIR/toolchain/tmp"
  # I don't love curling this out of something we'll download later but its how they do it and we haven't cloned the repo yet
  # https://issues.chromium.org/issues/40243622

  if [[ "$CHROMIUM_VERSION_TAG" == "88.0.4324.150" ]]; then
    util_error "Script exiting as 88.0.4324.150's build script doesn't seem to function, look at 02-init_tools.sh if important"
    #### THIS IS WHAT IT WAS:

    curl -s https://chromium.googlesource.com/chromium/src/+/$CHROMIUM_VERSION_TAG/build/install-build-deps.sh?format=TEXT \
    | base64 -d > $MAIN_DIR/toolchain/tmp/install-build-deps.sh
    if $SHOW; then
      echo -e "\n\nSee file in $MAIN_DIR/toolchain/tmp/install-build-deps.sh"
      exit 0
    fi
    chmod +x "$MAIN_DIR/toolchain/tmp/install-build-deps.sh"
    "$MAIN_DIR/toolchain/tmp/install-build-deps.sh" --no-syms --no-arm --no-chromeos-fonts --no-nacl --no-prompt
  elif [[ "$CHROMIUM_VERSION_TAG" == "126.0.6478.126" ]] || $TRY; then
    curl -s https://chromium.googlesource.com/chromium/src/+/$CHROMIUM_VERSION_TAG/build/install-build-deps.sh?format=TEXT \
    | base64 -d > $MAIN_DIR/toolchain/tmp/install-build-deps.sh
    curl -s https://chromium.googlesource.com/chromium/src/+/$CHROMIUM_VERSION_TAG/build/install-build-deps.py?format=TEXT \
    | base64 -d > $MAIN_DIR/toolchain/tmp/install-build-deps.py
    if $SHOW; then
      echo -e "\n\nSee file in $MAIN_DIR/toolchain/tmp/install-build-deps.sh"
      echo -e "\n\nSee file in $MAIN_DIR/toolchain/tmp/install-build-deps.py"
      exit 0
    fi
    chmod +x "$MAIN_DIR/toolchain/tmp/install-build-deps.sh"
    chmod +x "$MAIN_DIR/toolchain/tmp/install-build-deps.py"
    DEBIAN_FRONTEND=noninteractive "$MAIN_DIR/toolchain/tmp/install-build-deps.sh" --no-syms --no-arm --no-chromeos-fonts --no-nacl --no-prompt

  else
    util_error "No elif branch in 02-init_tools.sh for this version $CHROMIUM_VERSION_TAG, as of today, you still have to add the branch manually. You can add an elif statement right where you find this error, so search for it."
  fi
  # runhooks? i don't think we need to TODO but mentioned
  $NO_VERBOSE || echo "Downloaded and installed build-deps."
elif [[ "$PLATFORM" == "OSX" ]]; then
  $NO_VERBOSE || echo "Did nothing for OSX, we will have to do something, probably the same as linux." # TODO
fi
