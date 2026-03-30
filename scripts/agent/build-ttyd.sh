#! /bin/bash
set -e

# This script should be executed on an x86-64 host,
# as it uses a custom cross-build toolchain based on musl.
if [[ "$(uname -m)" != "x86_64" ]]; then
  echo "This script must be executed on an x86-64 host."
  exit 1
fi

builder_dockerfile=$(cat <<'EOF'
FROM ubuntu:20.04
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update
RUN apt-get install -y autoconf automake build-essential cmake curl file libtool
RUN apt-get install -y git
EOF
)

build_script=$(cat <<'EOF'
#!/bin/bash
mkdir -p dist

# Download ttyd source.
git clone https://github.com/tsl0922/ttyd.git
cd ttyd
git checkout eccebc6bb1dfbaf0c46f1fd9c53b89abc773784d

# Apply custom patch.
git apply /workspace/patch.diff

# Run build script.
env BUILD_TARGET=x86_64 ./scripts/cross-build.sh
./build/ttyd --version
cp ./build/ttyd /workspace/dist/ttyd_linux.x86_64.bin
env BUILD_TARGET=aarch64 ./scripts/cross-build.sh
cp ./build/ttyd /workspace/dist/ttyd_linux.aarch64.bin

# The script requires sudo to bootstrap a crossbuild toolchain.
chown -R ${BUILDER_UID}:${BUILDER_GID} /workspace/dist
chown -R ${BUILDER_UID}:${BUILDER_GID} .
EOF
)

patch_diff=$(cat <<'EOF'
diff --git a/scripts/cross-build.sh b/scripts/cross-build.sh
index d520d3a..45ce5e9 100755
--- a/scripts/cross-build.sh
+++ b/scripts/cross-build.sh
@@ -85,6 +85,8 @@ build_libwebsockets() {
     echo "=== Building libwebsockets-${LIBWEBSOCKETS_VERSION} (${TARGET})..."
     curl -fSsLo- "https://github.com/warmcat/libwebsockets/archive/v${LIBWEBSOCKETS_VERSION}.tar.gz" | tar xz -C "${BUILD_DIR}"
     pushd "${BUILD_DIR}/libwebsockets-${LIBWEBSOCKETS_VERSION}"
+        sed -i 's/context->default_retry.secs_since_valid_ping = 300/context->default_retry.secs_since_valid_ping = 20/g' lib/core/context.c
+        sed -i 's/context->default_retry.secs_since_valid_hangup = 310/context->default_retry.secs_since_valid_hangup = 30/g' lib/core/context.c
         sed -i 's/ websockets_shared//g' cmake/libwebsockets-config.cmake.in
         sed -i 's/ OR PC_OPENSSL_FOUND//g' lib/tls/CMakeLists.txt
         sed -i '/PC_OPENSSL/d' lib/tls/CMakeLists.txt
EOF
)

SCRIPT_DIR=$(cd `dirname "${BASH_SOURCE[0]}"` && pwd)
temp_dir=$(mktemp -d -t ttyd-build.XXXXX)
echo "Using temp directory: $temp_dir"
echo "$build_script" > "$temp_dir/build.sh"
echo "$patch_diff" > "$temp_dir/patch.diff"
chmod +x $temp_dir/*.sh
echo "$builder_dockerfile" > "$SCRIPT_DIR/ttyd-builder.dockerfile"

docker build -t ttyd-builder \
  -f $SCRIPT_DIR/ttyd-builder.dockerfile $SCRIPT_DIR

docker run --rm -it \
  -w /workspace \
  -e BUILDER_UID=$(id -u) \
  -e BUILDER_GID=$(id -g) \
  -v $temp_dir:/workspace \
  ttyd-builder \
  /workspace/build.sh

ls -lh "$temp_dir/dist/"
cp $temp_dir/dist/ttyd*.bin $SCRIPT_DIR/../../src/ai/backend/runner
rm -rf "$temp_dir"
