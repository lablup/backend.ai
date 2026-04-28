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

# Update external tool binaries (bssh, all-smi, etc.)
echo "Updating external tool binaries..."
./scripts/download-external-tools.sh
# Only commit if there are staged changes (download-external-tools.sh may be a no-op)
if ! git diff --cached --quiet; then
    git commit -m "chore: update external tool binaries"
else
    echo "No external tool binary updates to commit."
fi

# Update VERSION file
echo $TARGET_VERSION > VERSION

# Freeze NEXT_RELEASE_VERSION references to the actual version string.
# Skip for pre-release versions (PEP 440: rc, a, b, dev, post) so the
# placeholder survives until the eventual stable release is cut.
if [[ "$TARGET_VERSION" =~ (rc|a|b|dev|post)[0-9]+ ]]; then
    echo "Skipping NEXT_RELEASE_VERSION freeze for pre-release version ${TARGET_VERSION}"
else
    echo "Freezing NEXT_RELEASE_VERSION to ${TARGET_VERSION}..."
    python3 scripts/freeze_release_version.py "${TARGET_VERSION}"
    pants fix ::
    pants fmt ::
fi

# Update the changelog (--yes consumes news fragments without an interactive prompt)
LOCKSET=towncrier/$(yq '.python.interpreter_constraints[0] | split("==") | .[1]' pants.toml) ./py -m towncrier --yes

# Update sample config files (unmask secrets to show actual default values)
./backend.ai mgr config generate-sample --overwrite --unmask-secrets
./backend.ai ag config generate-sample --overwrite --unmask-secrets
./backend.ai storage config generate-sample --overwrite --unmask-secrets
./backend.ai web config generate-sample --overwrite --unmask-secrets

./backend.ai mgr api dump-openapi --output docs/manager/rest-reference/openapi.json
./scripts/generate-graphql-schema.sh

# Check dependencies
pants tailor --check update-build-files --check '::'
pants check ::

git add -A
git commit -m "release: $TARGET_VERSION"
