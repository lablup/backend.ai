#! /bin/bash
pants --tag='scie' --tag='lazy' package '::'
# NOTE: 'pants run' does not support parallelization
pants list --filter-tag-regex='checksum' '::' | xargs -n 1 pants run

OS_TYPE=$(uname -s)
CPU_ARCH=$(uname -m)
SYSTEM="$OS_TYPE $CPU_ARCH"
case "$SYSTEM" in
  "Linux x86_64" )
    SRC_PLATFORM="linux-x64"
    DST_PLATFORM="linux-x86_64"
    CHECKSUM_CMD="sha256sum"
    ;;
  "Linux aarch64" )
    SRC_PLATFORM="linux-arm64"
    DST_PLATFORM="linux-aarch64"
    CHECKSUM_CMD="sha256sum"
    ;;
  "Darwin x86_64" )
    SRC_PLATFORM="macos-x64"
    DST_PLATFORM="macos-x86_64"
    CHECKSUM_CMD="shasum -a 256"
    ;;
  "Darwin arm64" )
    SRC_PLATFORM="macos-arm64"
    DST_PLATFORM="macos-aarch64"
    CHECKSUM_CMD="shasum -a 256"
    ;;
esac

