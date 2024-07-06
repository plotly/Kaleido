set -e

# Lets get main directory
MAIN_DIR="$(git rev-parse --show-toplevel)"
if [ "${MAIN_DIR}" == "" ] || [ "${MAIN_DIR}" == "/" ]; then
  echo "We need to be in the git directory." >&2
  exit 1
fi
BIN_DIR="$(realpath $MAIN_DIR/bin)"
bash -c '(
  MAIN_DIR="$(git rev-parse --show-toplevel)"
  if [ "${MAIN_DIR}" == "" ] || [ "${MAIN_DIR}" == "/" ]; then
    echo "We need to be in the git directory." >&2
    exit 1
  fi
  BIN_DIR="$(realpath $MAIN_DIR/bin)"
  mkdir -p "${BIN_DIR}"

  make_link()
  {
    name="${1//[0-9]*-/}"
    name=${name%.sh}
    ln -fs "$MAIN_DIR/toolchain/stages/$1" "$BIN_DIR/$name"
  }

  make_link 00-set_version.sh
  make_link 01-fetch_tools.sh
)'

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  echo "You may rerun this script using \`source\` to modify your shell's path or, on your command line, run:"
  echo "export PATH=\"${BIN_DIR}:\$PATH\""
  exit 0
fi

export PATH="$BIN_DIR:$PATH"
