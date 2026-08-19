#!/bin/bash

usage() {
    echo "Usage: $0 [--lts] <target_version> [webui_version]"
    echo "  --lts  the release line being cut is a long-term support one;"
    echo "         only meaningful for an X.Y.0rc1 target, which cuts a line"
}

LTS_ARG=()
POSITIONAL=()
while [ "$#" -gt 0 ]; do
    case "$1" in
        --lts) LTS_ARG=(--lts) ;;
        -h|--help) usage; exit 0 ;;
        -*) echo "Error: unknown option: $1"; usage; exit 1 ;;
        *) POSITIONAL+=("$1") ;;
    esac
    shift
done
set -- "${POSITIONAL[@]}"

# Check if at least target version is provided
if [ "$#" -lt 1 ]; then
    echo "Error: Target version is required"
    usage
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

# Update the version-branch changelog (consumes news fragments without an interactive prompt)
python3 scripts/run-towncrier.py "${TARGET_VERSION}"

# Update sample config files (unmask secrets to show actual default values)
./backend.ai mgr config generate-sample --overwrite --unmask-secrets
./backend.ai ag config generate-sample --overwrite --unmask-secrets
./backend.ai storage config generate-sample --overwrite --unmask-secrets
./backend.ai web config generate-sample --overwrite --unmask-secrets

./backend.ai mgr api dump-openapi --output docs/manager/rest-reference/openapi.json
./scripts/generate-graphql-schema.sh

# Keep the maintained-versions registry in step. Only an `X.Y.0rc1` target cuts
# a release line, so this is a no-op for every other release; it also retires
# the lines that are due.
.github/scripts/update-maintained-versions.sh "${TARGET_VERSION}" "${LTS_ARG[@]}"

# Check dependencies
pants tailor --check update-build-files --check '::'
pants check ::

git add -A
git commit -m "release: $TARGET_VERSION"

# Advance NEXT_RELEASE_VERSION to the next sprint development cycle.
# Only for sprint releases (patch == 0); the regex also excludes patch
# releases and PEP 440 pre-releases (rc/a/b/dev/post). Override the computed
# sprint+1 default with NEXT_DEV_VERSION (e.g. for year rollover: 27.1.0).
if [[ "$TARGET_VERSION" =~ ^[0-9]+\.[0-9]+\.0$ ]]; then
    next_dev=$(python3 scripts/bump_next_release_version.py ${NEXT_DEV_VERSION:+"$NEXT_DEV_VERSION"})
    git add src/ai/backend/common/meta/meta.py
    git commit -m "chore: bump NEXT_RELEASE_VERSION to $next_dev"
fi
