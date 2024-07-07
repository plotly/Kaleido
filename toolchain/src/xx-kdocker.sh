#!/bin/bash
set -e
set -u

# Please do your flags first so that utilities uses $NO_VERBOSE, otherwise failure!

IMAGE="cimg/python:3.12.3"
usage=(
  "kdocker is convenience script to start dockers for building on linux."
  ""
  "You need to be in the docker group to run it. Script pulls an image and ads"
  "the user who ran the script the docker, and mount the project directory as well."
  "See bottom for tips on detaching and reattaching to the docker."
  ""
  "Usage (DO NOT USE --long-flags=something, just --long-flag something):"
  "You can always try -v or --verbose"
  ""
  "Display this help:"
  "kdocker [-h|--h]"
  ""
  "kdocker [-i|--image IMAGE] [-d|--detach] [[-g|--git]|[-r|--repo REPO]] COMMAND"
  ""
  "-i|--image IMAGE   IMAGE will be used instead of the default, $IMAGE."
  "                   If this is not the same as circle-ci, please submit a pull request"
  "                   updating this script"
  ""
  "-d|--detach        This will run the container and immediately detach."
  "                   The container will also exit immediately after finishing."
  ""
  "-g|--git           The default behavior is to mount your plotly/kaleido git folder"
  "                   into the docker, but this will try to re-clone it instead. Your"
  "                   current working directory will be mounted into project/."
  ""
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
COMMAND="sudo apt-get update; sudo useradd --uid=$UID --shell /bin/bash --create-home $USER; echo '$USER ALL=NOPASSWD: ALL' | sudo tee -a /etc/sudoers.d/50-circleci &> /dev/null;"
USER_COMMAND='export PATH+=:~/kaleido/bin/; '
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

VOLUME="$MAIN_DIR:/home/$USER/kaleido"
if $CLONE; then
  USER_COMMAND+="git clone $REPO; "
  VOLUME="$(pwd):/home/$USER/"
fi
if [[ -n "${@}" ]]; then
  USER_COMMAND+="${@}; "
fi
COMMAND+="echo '$USER_COMMAND' | sudo tee -a /home/$USER/.temp_script.sh &> /dev/null; echo . /home/$USER/.temp_script.sh | sudo tee -a /home/$USER/.bash_login &> /dev/null; "
COMMAND+="sudo su - $USER"

docker pull $IMAGE
docker container run --rm -it$DETACH -v "$VOLUME" "$IMAGE" bash -c "$COMMAND"
