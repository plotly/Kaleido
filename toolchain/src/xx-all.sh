set -e
set -u
SCRIPT_DIR=$( cd -- "$( dirname -- $(readlink -f -- "${BASH_SOURCE[0]}") )" &> /dev/null && pwd )
$SCRIPT_DIR/00-set_version.sh $@
$SCRIPT_DIR/01-fetch_tools.sh $@
