#!/bin/bash

# Check if both versions are provided
if [ "$#" -ne 2 ]; then
    echo "Error: Both target version and webui version are required"
    echo "Usage: $0 <target_version> <webui_version>"
    exit 1
fi

TARGET_VERSION=$1
WEBUI_VERSION=$2

echo "Preparing release for version ${TARGET_VERSION} (WebUI: ${WEBUI_VERSION})"

git checkout -b "release/$TARGET_VERSION"

./scripts/download-webui-release.sh $WEBUI_VERSION

git commit -m "chore: update webui to $WEBUI_VERSION"

# Check dependencies
pants tailor --check update-build-files --check '::'
pants check ::

# Update VERSION file
echo $TARGET_VERSION > VERSION

# Update the documentations
./backend.ai mgr api dump-gql-schema --output docs/manager/graphql-reference/schema.graphql
./backend.ai mgr api dump-openapi --output docs/manager/rest-reference/openapi.json

# Update the changelog
LOCKSET=towncrier/$(yq '.python.interpreter_constraints[0] | split("==") | .[1]' pants.toml) ./py -m towncrier

git add -A
git commit -m "release: $TARGET_VERSION"
