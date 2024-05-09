#! /bin/bash
OS_TYPE=$(uname -s)
CPU_ARCH=$(uname -m)
SYSTEM="$OS_TYPE $CPU_ARCH"
case "$SYSTEM" in
  "Linux x86_64" )
    PLATFORM="linux-x86_64"
    ;;
  "Linux aarch64" )
    PLATFORM="linux-aarch64"
    ;;
  "Darwin x86_64" )
    PLATFORM="macos-x86_64"
    ;;
  "Darwin arm64" )
    PLATFORM="macos-aarch64"
    ;;
  * )
    echo "Sorry, Backend.AI does not support this platform."
    exit 1
    ;;
esac

# TODO: add GitHub release download
curl -L https://bnd.ai/installer-stable-"${PLATFORM}" -o "backendai-install-${PLATFORM}"
chmod +x "backendai-install-${PLATFORM}"

exec "./backendai-install-${PLATFORM}" install "$@"
