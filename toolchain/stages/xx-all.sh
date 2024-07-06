set -e
set -u
./00-set_version.sh $@
./01-fetch_tools.sh $@
