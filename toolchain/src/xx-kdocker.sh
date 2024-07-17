#!/bin/bash
# This is a script to help get us into a workable dev-environment inside a docker container
# ⚠️⚠️⚠️ HERE BE DRAGONS ⚠️⚠️⚠️
#    \****__              ____
#      |    *****\_      --/ *\-__
#      /_          (_    ./ ,/----'
#           \__         (_./  /
#              \__           \___----^__
#               _/   _                  \
#        |    _/  __/ )\"\ _____         *\
#        |\__/   /    ^ ^       \____      )
#         \___--"                    \_____ )
#
# ASCII Credit: IronWing

set -e
set -u

# Please do your flags first so that utilities uses $NO_VERBOSE, otherwise failure!

IMAGE="${IMAGE-cimg/python:3.12.3}"
usage=(
  "kdocker is convenience script to start dockers for building on linux."
  ""
  "You need to be in the docker group to run kdocker. kdocker 1) pulls an image 2) adds"
  "the user who ran kdocker, 3) mounts the project directory to /usr/share/kaleido."
  "See bottom for tips on detaching and reattaching to the docker."
  ""
  "Usage (DO NOT USE --long-flags=something, just --long-flag something):"
  "You can always try -v or --verbose"
  ""
  "Display this help:"
  "kdocker [-h|--h]"
  ""
  "kdocker [-u USER] [-i|--image IMAGE] [-d|--detach] COMMAND"
  ""
  "-u|--user USER     If you are running kdocker as sudo, you can use this to specify which"
  "                   user you normally are."
  ""
  "-i|--image IMAGE   IMAGE will be used instead of the default, $IMAGE."
  "                   If this is not the same as circle-ci, please submit a pull request"
  "                   updating this script"
  ""
  "-d|--detach        This will run the container and immediately detach."
  "                   The container will also exit immediately after finishing."
  ""
  "-c|--copy          This will reclone your git project to ~/kaleido and also patch over"
  "                   all uncommited, staged and unstaged, tracked changes. Untracked changes"
  "                   will not be cloned over. "
  "                   Hint: Use \`git add -N PATH\` to track files without staging them for commit."
  "                   Hint: Don't work out of the clone ~/kaleido directory."
  "                   Hint: Its easier to push outside of docker."
  "                   Hint: Use \`krefresh\` to re-clone/patch ~/kaleido after changes."
  "                   Hint: If you use -c (or \`krefresh\`), kaleido build commands (set_version, etc)"
  "                         will always be run from ~/kaleido, not /usr/share/kaleido. So all changes"
  "                         need to be \`krefresh\`ed."
  "Docker tips:"
  "      Ending the first session will always end the docker. \`ctl+d\` will exit bash and session."
  "     \`ctl+p ctl+q\` (instead of \`ctl+d\`) will leave bash running. You can reattach to (only)"
  "      the first session with: \`docker attach CONTAINER_NAME\`. Containers can be listed with"
  "     \`docker container ls\`. You can get a new secondary session with:"
  "     \`docker exec --user \$USER -it CONTAINER_NAME bash\`."
)

FLAGS=(":" "-c" "--copy" "-d" "--detach")
ARGFLAGS=("-i" "--image" "-u" "--user")

SCRIPT_DIR="$( cd -- "$( dirname -- $(readlink -f -- "${BASH_SOURCE[0]}") )" &> /dev/null && pwd )"
. "$SCRIPT_DIR/include/utilities.sh"

$(flags_resolve "false" "-d" "--detach") && DETACH=d || DETACH=""
$NO_VERBOSE || echo "Detach flag: '$DETACH'"

COPY="$(flags_resolve "false" "-c" "--copy")"
$NO_VERBOSE || echo "Copy: $COPY"

IMAGE=$(flags_resolve "${IMAGE}" -i --image)
$NO_VERBOSE || echo "Image: $IMAGE"

LOCAL_USER=$(flags_resolve "${USER}" -u --user)

$NO_VERBOSE || echo "Running xx-kdocker.sh"

LOCAL_UID="$(id -u "$LOCAL_USER")"
$NO_VERBOSE || echo "User: $LOCAL_USER w/ ID $LOCAL_UID"

# Set up mounting some of our directories into docker
VOLUME="$MAIN_DIR:/usr/share/kaleido"

APT_CACHE="$MAIN_DIR/toolchain/tmp/apt_cache/"
mkdir -p "$APT_CACHE"
APT_VOLUME="$APT_CACHE:/var/lib/apt/lists/"


# COMMAND is what we run to set up the user and do some basics
COMMAND="sudo apt-get update; sudo apt-get install rsync; sudo useradd --uid=$LOCAL_UID --shell /bin/bash --create-home $LOCAL_USER; echo '$LOCAL_USER ALL=NOPASSWD: ALL' | sudo tee -a /etc/sudoers.d/50-circleci &> /dev/null; "

# USER_COMMAND is what we run once we are logged in as the intended user,
# including the actual user's desired command
# \$PATH means we don't want to expand path now, but in docker, it makes it to USER_COMMAND as $PATH, literally
USER_COMMAND="export PATH=/home/$LOCAL_USER/kaleido/bin:\$PATH; "

# ":" is the bash noop, it is also the key for extra user arguments
# so this prints ":" if it can't find an argument of key ":"
USER_COMMAND+="$(flags_resolve ":" ":"); " # if the user passed \$VAR, it will make it to USER_COMMAND as $VAR, literally

# Let's grab the users git config so they can use it in docker.
# We could mount, but we copy
# They won't have ssh though, so only commit, no push
gitconfig="$(cat /home/$LOCAL_USER/.gitconfig)"

# Some short cuts to make this less or maybe more readable
sudo="sudo sudo -u $LOCAL_USER" # will throw background errors in docker, is fine
silence="1> /dev/null"
if ! $NO_VERBOSE; then
  silence=""
fi
bash_login="/home/$LOCAL_USER/.bash_login"
temp_script="/home/$LOCAL_USER/.temp_script.sh"

# Understanding bash expansion rules:
# KEY="value"
#
# echo "$KEY"
# value
#
# echo '$KEY'
# $KEY
#
# echo "'$KEY'"
# 'value'
#
# So while $USER_COMMAND is expanded to the bash command,
# When it is echos, it will be between '', so it will echo literaly to the file
# Which will later be executed, and then will be expanded
COMMAND+="\
  echo '$USER_COMMAND' | $sudo tee -a $temp_script $silence; \
  echo 'touch $temp_script' | $sudo tee -a $bash_login $silence; \
  echo '. $temp_script' | $sudo tee -a $bash_login $silence; \
  echo 'rm -f $temp_script &> /dev/null' | $sudo tee -a $bash_login $silence; \
  echo '$gitconfig' | $sudo tee -a /home/$LOCAL_USER/.gitconfig $silence; "

COMMAND+="sudo ln -s /usr/share/kaleido/toolchain/src/xx-krefresh.sh /usr/bin/krefresh $silence; "
COMMAND+="sudo chmod o+rx /usr/bin/krefresh; "

if $COPY; then
  $NO_VERBOSE || echo "Copy set"
  COMMAND+="echo 'export MAIN_DIR=\"/home/$LOCAL_USER/kaleido\"' | $sudo tee -a $bash_login $silence; "
  if $NO_VERBOSE; then
    COMMAND+="$sudo krefresh -q -a --force &> /dev/null; "
  else
    COMMAND+="$sudo krefresh -q -a --force; "
  fi
fi
COMMAND+="\
  $sudo cp $bash_login ${HOME}/.bash_login.log; \
  $sudo cp $temp_script ${HOME}/.temp_script.sh.log; "

COMMAND+="sleep 1; sudo -E su - $LOCAL_USER; "

$NO_VERBOSE || echo -e "User Command Set:\n$USER_COMMAND"
$NO_VERBOSE || echo -e "Command Set:\n$COMMAND"

$NO_VERBOSE || echo "Pulling $IMAGE"
docker pull "$IMAGE"

$NO_VERBOSE || set -x # to print out the line w/o rewriting it
docker container run -e "TERM=$TERM" --rm -it$DETACH -v "$APT_VOLUME" -v "$VOLUME" "$IMAGE" bash -c "$COMMAND"
