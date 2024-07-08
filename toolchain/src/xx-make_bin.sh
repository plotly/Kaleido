# Lets get main directory

NO_PATH=false
if [[ "$1" == "--no-path" ]] || [[ "$1" == "-n" ]]; then
  NO_PATH=true
  shift
fi
if [[ "$1" != "" ]]; then
  echo "make_bin takes one optional flag: -n|--no-path to skip setting the path"
  exit 1;
fi

MAIN_DIR="$(git rev-parse --show-toplevel)"
if [[ "${MAIN_DIR}" == "" ]] || [[ "${MAIN_DIR}" = "/" ]]; then
  echo "We need to be in the git directory." >&2
  exit 1
fi
BIN_DIR="$(realpath $MAIN_DIR/bin)"
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

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  echo "You may rerun this script using \`source\` to modify your shell's path or, on your command line, run:"
  echo "export PATH=\"${BIN_DIR}:\$PATH\""
  exit 0
fi

export PATH="$BIN_DIR:$PATH"
