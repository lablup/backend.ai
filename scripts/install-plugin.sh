#! /bin/bash

mkdir -p ./plugins
PLUGIN_BRANCH=${PLUGIN_BRANCH:-main}
PLUGIN_OWNER=$(echo $1 | cut -d / -f 1)
PLUGIN_REPO=$(echo $1 | cut -d / -f 2)
git clone "https://github.com/$1" "./plugins/$PLUGIN_REPO"
