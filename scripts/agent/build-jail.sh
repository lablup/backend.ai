#! /bin/bash
set -e

arch=$(uname -m)
distros=("ubuntu18.04" "ubuntu20.04" "ubuntu22.04" "alpine3.8" "centos" "centos8.0")

SCRIPT_DIR=$(cd `dirname "${BASH_SOURCE[0]}"` && pwd)
temp_dir=$(mktemp -d -t bai-jail.XXXXX)
cd "$temp_dir"
echo "Using temp directory: $temp_dir"

git clone https://github.com/lablup/backend.ai-jail jail
cd jail

for distro in "${distros[@]}"; do
  if ! make $distro; then
    echo "Warning: make $distro failed"
  else
    cp out/jail.$distro.$arch.bin        $SCRIPT_DIR/../../src/ai/backend/runner
  fi
done
cd ..

ls -l .

rm -rf "$temp_dir"
