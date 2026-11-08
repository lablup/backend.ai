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
# Skip for pre-release versions (PEP 440: rc, a, b, dev) so the placeholder
# survives until the eventual stable release is cut. A `post` re-release is a
# final release, so it freezes.
if [[ "$TARGET_VERSION" =~ (rc|a|b|dev)[0-9]+ ]]; then
    echo "Skipping NEXT_RELEASE_VERSION freeze for pre-release version ${TARGET_VERSION}"
else
    echo "Freezing NEXT_RELEASE_VERSION to ${TARGET_VERSION}..."
    python3 scripts/freeze_release_version.py "${TARGET_VERSION}"
    RUFF_VERSION=$(scripts/pyscript.sh scripts/tomltool.py -f pants.toml get 'ruff.version')
    FROZEN=()
    while IFS= read -r -d '' f; do
        FROZEN+=("$f")
    done < <(git diff --name-only -z -- 'src/*.py')
    if [ ${#FROZEN[@]} -gt 0 ]; then
        uvx "ruff@${RUFF_VERSION}" check --fix --exit-zero --quiet --force-exclude "${FROZEN[@]}"
        uvx "ruff@${RUFF_VERSION}" format --quiet --force-exclude "${FROZEN[@]}"
    fi
fi

# Give the news fragments named without a PR number their PR number
python3 scripts/rename-changelog-fragments.py || exit 1

# Update the version-branch changelog (consumes news fragments without an interactive prompt)
python3 scripts/run-towncrier.py "${TARGET_VERSION}" || exit 1

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

git add -A
git commit -m "release: $TARGET_VERSION"
