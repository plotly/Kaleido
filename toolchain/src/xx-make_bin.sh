#!/bin/bash
set -e
set -u

# Please do your flags first so that utilities uses $NO_VERBOSE, otherwise failure!
usage=(
  "xx-make_bin.sh will create shortcuts to the utilties and tell you how to set your path."
  ""
  "Usage (DO NOT USE --long-flags=something, just --long-flag something):"
  "You can always try -v or --verbose"
  ""
  "Display this help:"
  "xx-make_bin [-h|--h]"
  ""
  "You can skip the path recommendation:"
  "xx_template [-n|--no-path]"
)
# Lets get main directory

FLAGS=("-n" "--no-path")
ARGFLAGS=()

SCRIPT_DIR="$( cd -- "$( dirname -- $(readlink -f -- "${BASH_SOURCE[0]}") )" &> /dev/null && pwd )"
. "$SCRIPT_DIR/include/utilities.sh"

NO_PATH="$(flags_resolve false "-n" "--no-path")"

$NO_VERBOSE || echo "Running xx-make_bin.sh"

BIN_DIR="$(realpath $MAIN_DIR/bin)"

# really awful way to make sure this is bash lol
bash -c '(
  MAIN_DIR="$(git rev-parse --show-toplevel)"
  if [[ "${MAIN_DIR}" == "" ]] || [[ "${MAIN_DIR}" == "/" ]]; then
    echo "We need to be in the git directory." >&2
    exit 1
  fi
  BIN_DIR="$(realpath $MAIN_DIR/bin)"
  mkdir -p "${BIN_DIR}"

  make_link()
  {
    name="${1//[0-9x]*-/}"
    name=${name%.sh}
    echo "linking $MAIN_DIR/toolchain/src/$1 $BIN_DIR/$name"
    ln -fs "../toolchain/src/$1" "$BIN_DIR/$name"
  }
  shopt -s extglob
  for script in $MAIN_DIR/toolchain/src/[0-9]*-*.sh; do
    make_link "$(basename -- $script)"
  done
  make_link "xx-kdocker.sh"
  make_link "xx-all.sh"
)'

if $NO_PATH; then exit 0; fi

echo "You should run:"
echo "export PATH=\"${BIN_DIR}:\$PATH\""
