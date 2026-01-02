#!/bin/bash

# Check if at least target version is provided
if [ "$#" -lt 1 ]; then
    echo "Error: Target version is required"
    echo "Usage: $0 <target_version> [webui_version]"
    exit 1
fi

TARGET_VERSION=$1
WEBUI_VERSION=$2

if [ "$#" -eq 1 ]; then
    echo "Preparing release for version ${TARGET_VERSION} (skipping WebUI update)"
    git checkout -b "release/$TARGET_VERSION"
else
    echo "Preparing release for version ${TARGET_VERSION} (WebUI: ${WEBUI_VERSION})"
    git checkout -b "release/$TARGET_VERSION"
    ./scripts/download-webui-release.sh $WEBUI_VERSION
    git commit -m "chore: update webui to $WEBUI_VERSION"
fi

# Check dependencies
pants tailor --check update-build-files --check '::'
pants check ::

# Update VERSION file
echo $TARGET_VERSION > VERSION

# Update the changelog
LOCKSET=towncrier/$(yq '.python.interpreter_constraints[0] | split("==") | .[1]' pants.toml) ./py -m towncrier

# Update sample config files
./backend.ai mgr config generate-sample --overwrite
./backend.ai ag config generate-sample --overwrite
./backend.ai storage config generate-sample --overwrite
./backend.ai web config generate-sample --overwrite

./scripts/generate-graphql-schema.sh

git add -A
git commit -m "release: $TARGET_VERSION"
