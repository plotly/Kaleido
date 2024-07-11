#!/bin/bash
set -e
set -u

if test -d /usr/share/kaleido; then
  :
else
  echo "Only run from within docker from kdocker 1>&2"
  exit 1
fi
(
  cd /usr/share/kaleido
  usage=(
    "krefresh is a utility to incremently modify the kaleido repository without necessarily prompting a full rebuild."
    "It is only to be used within kdocker, and is better to be used with '-c|--copy'"
    ""
    "Usage (DO NOT USE --long-flags=something, just --long-flag something):"
    "You can always try -v or --verbose"
    ""
    "Display this help:"
    "krefresh [-h|--h]"
    ""
    "Skip confirmation"
    "krefresh [-f|--force]"
    ""
    "Completely erase ~/kaleido and replace"
    "krefresh [-a|--all]"
    ""
  )

  FLAGS=("-q" "-f" "--force" "-a" "--all")
  ARGFLAGS=()

  . "/usr/share/kaleido/toolchain/src/include/utilities.sh"

  FORCE="$(flags_resolve false "-f" "--force")"
  ALL="$(flags_resolve false "-a" "--all")"
  QUIET="$(flags_resolve false "-q")"

  $NO_VERBOSE || echo "Running xx-krefresh.sh"

  echo "Force? $FORCE"
  REPLY='Y'
  if ! $FORCE; then
    read -p "Are you sure? (Y/n)" -n 1 -r
    echo
  fi
  if [[ ! "$REPLY" =~ ^[Yy]$ ]] && [[ "$REPLY" != "" ]]; then
    exit 0
  fi

  if $ALL; then
    echo "removing current..."
    rm -rf ${HOME}/kaleido 2> /dev/null
  fi

  if test -d ${HOME}/kaleido/.git; then
    echo "Cleaning.."
    git -C ${HOME}/kaleido/ clean -fdd
    echo "Restoring..."
    git -C ${HOME}/kaleido/ restore .
    echo "Pulling"
    git -C ${HOME}/kaleido/ pull

  else
    echo "cloning..."
    git clone /usr/share/kaleido ${HOME}/kaleido
  fi
  echo "calculating diff..."
  git -C /usr/share/kaleido diff -p HEAD > ${HOME}/.git_patch_1
  echo "patching..."
  git -C ${HOME}/kaleido apply ${HOME}/.git_patch_1 --allow-empty
  if ! $QUIET && [[ "${MAIN_DIR}" == "/usr/share/kaleido" ]]; then
    echo "       !!!! Set the main github repo to the copy clone!!!!!"
    echo "       All temporary files should be copied there, keep your main clone clean."
    echo ""
    echo "       export MAIN_DIR=\"${HOME}/kaleido\""
    echo "       !!!!"
  fi
  bash -c "cd ${HOME}/kaleido && ./toolchain/src/xx-make_bin.sh -n"
)
