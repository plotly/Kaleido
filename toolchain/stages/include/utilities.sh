#!/bin/bash

set -e # exit on any error

error()
{
    echo "Error: $@" >&2
    exit 1
}
export -f error

export MAIN_DIR="$(git rev-parse --show-toplevel)" # let's get base directory

if [ "$MAIN_DIR" == "" ] || [ "$MAIN_DIR" == "/" ]; then
  error "git rev-parse returned an empty directory, are we in a git directory?"
fi
