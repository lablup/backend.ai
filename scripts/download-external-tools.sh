#!/bin/bash
# Download latest external tool binaries for Backend.AI runner

set -euo pipefail

BASE_PATH=$(cd "$(dirname "$0")"/.. && pwd)
TARGET_DIR="${BASE_PATH}/src/ai/backend/runner"
WORK_DIR=$(mktemp -d)
trap 'rm -rf "${WORK_DIR}"' EXIT

download_github_release() {
    local repo=$1
    local binary_name=$2
    local tag=$3

    if [ -z "$tag" ]; then
        echo "Fetching latest release tag for ${repo}..."
        tag=$(curl -fsSL "https://api.github.com/repos/${repo}/releases/latest" | jq -r .tag_name)
    fi
    echo "Downloading ${binary_name} ${tag} from ${repo}..."

    for ARCH in aarch64 x86_64; do
        local url="https://github.com/${repo}/releases/download/${tag}/${binary_name}-linux-${ARCH}-musl.tar.gz"
        local extract_dir="${WORK_DIR}/${binary_name}-${ARCH}"
        mkdir -p "${extract_dir}"
        echo "  ${ARCH}: ${url}"
        curl -fL -o "${extract_dir}/archive.tar.gz" "$url"
        tar -xzf "${extract_dir}/archive.tar.gz" -C "${extract_dir}"
        mv "${extract_dir}/${binary_name}" "${TARGET_DIR}/${binary_name}.${ARCH}.bin"
        chmod +x "${TARGET_DIR}/${binary_name}.${ARCH}.bin"
        # Move manpage if exists
        if [ -f "${extract_dir}/${binary_name}.1" ]; then
            mv "${extract_dir}/${binary_name}.1" "${TARGET_DIR}/"
        fi
    done

    echo "  Updated ${binary_name} to ${tag}"
}

echo "=== Updating external tool binaries ==="

# bssh (SSH server for Backend.AI)
download_github_release "lablup/bssh" "bssh" "${BSSH_VERSION:-}"

# all-smi (GPU monitoring tool)
download_github_release "lablup/all-smi" "all-smi" "${ALL_SMI_VERSION:-}"

echo "=== All external tools updated ==="
git add "${TARGET_DIR}"/*.bin "${TARGET_DIR}"/*.1 2>/dev/null || true
