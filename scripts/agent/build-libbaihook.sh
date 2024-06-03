#! /bin/bash
set -e

arch=$(uname -m)
distros=("ubuntu18.04" "ubuntu20.04" "ubuntu22.04" "alpine" "centos" "centos8.0")

SCRIPT_DIR=$(cd `dirname "${BASH_SOURCE[0]}"` && pwd)
temp_dir=$(mktemp -d -t bai-libbaihook.XXXXX)
cd "$temp_dir"
echo "Using temp directory: $temp_dir"

git clone https://github.com/lablup/backend.ai-hook libbaihook
cd libbaihook

for distro in "${distros[@]}"; do
  if ! ./build.sh $distro; then
    echo "Warning: build $distro failed"
  else
    cp libbaihook.$distro.$arch.so        $SCRIPT_DIR/../../src/ai/backend/runner
  fi
done
cd ..

ls -l .

rm -rf "$temp_dir"
