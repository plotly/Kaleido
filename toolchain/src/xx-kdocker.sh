#!/bin/bash
set -e
set -u

# Please do your flags first so that utilities uses $NO_VERBOSE, otherwise failure!

IMAGE="cimg/python:3.12.3"
usage=(
  "kdocker is convenience script to start dockers for building on linux."
  "You need to be in the docker group to run it."
  ""
  "Usage (DO NOT USE --long-flags=something, just --long-flag something):"
  "You can always try -v or --verbose"
  ""
  "Display this help:"
  "kdocker [-h|--h]"
  ""
  "kdocker [-i|--image IMAGE] [-d|--detach] [[-g|--git]|[-r|--repo REPO]] COMMAND"
  "   We first run \`sudo apt-get update\`, so passing command \`./kaleido/my_script.sh\` makes:"
  "   \`sudo apt-get update; ./kaleido/my_script.sh\`."
  "   Your shell is then started as a subshell."
  ""
  "Recomended use is to run without flags, and to detach and attach to the session w/ \`docker\`."
  "See docker tips below."
  ""
  "Default behavior is to mount the git folder onto /home/circleci/project/kaleido".
  ""
  ""
  "-i|--image IMAGE   IMAGE will be used instead of the default, $IMAGE."
  "                   If this is not the same as circle-ci, please submit a pull request"
  "                   updating this script"
  ""
  "-d|--detach        This will run the container and immediately detach."
  "                   The container will also exit immediately after finishing."
  "-g|--git           The default behavior is to mount your plotly/kaleido git folder"
  "                   into the docker, but this will try to re-clone it instead. Your"
  "                   current working directory will be mounted into project/."
  "-r|--repo REPO     This is like --git, except it will run \`git clone REPO\`. You can pass"
  "                   flags and stuff in quotes: \`-r \"-b my_branch my_user/my_repo\"\`."
  "                   It will override -g."
  ""
  "Docker tips:"
  "      Ending the first session will always end the docker. \`ctl+d\` will exit bash and session."
  "     \`ctl+p ctl+q\` (instead of \`ctl+d\`) will leave bash running. You can reattach to (only)"
  "      the first session with: \`docker attach CONTAINER_NAME\`. Containers can be listed with"
  "     \`docker container ls\`. You can get a new secondary session with:"
  "     \`docker exec -it CONTAINER_NAME bash\`."
)

## PROCESS FLAGS
COMMAND="sudo apt-get update; "
DETACH=""
CLONE=false
NO_VERBOSE=true
REPO="plotly/kaleido"
while (( $# )); do
  case $1 in
    -h|--help)        printf "%s\n" "${usage[@]}"; exit 0  ;;
    -i|--image)       shift; IMAGE="$1"                    ;;
    -d|--detach)      DETACH="d"                           ;;
    -g|--git)         CLONE=true                           ;;
    -r|--repo)        shift; CLONE=true; REPO="$1"         ;;
    -v|--verbose)     NO_VERBOSE=false                     ;;
    *)                break;;
  esac
  shift
done

$NO_VERBOSE || echo "Running xx-kdocker.sh"

SCRIPT_DIR=$( cd -- "$( dirname -- $(readlink -f -- "${BASH_SOURCE[0]}") )" &> /dev/null && pwd )
. "$SCRIPT_DIR/include/utilities.sh"

# figure out persisting
# figure out exiting w/o
VOLUME="$MAIN_DIR:/home/circleci/project/kaleido"
if $CLONE; then
  COMMAND+="git clone $REPO; "
  VOLUME="$(pwd):/home/circleci/project/"
fi
if [[ -n "${@}" ]]; then
  COMMAND+="${@}; "
fi
COMMAND+="bash"

docker pull $IMAGE
docker container run --rm -it$DETACH -v "$VOLUME" "$IMAGE" bash -c "$COMMAND"
