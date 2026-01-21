#! /bin/bash
set -e

arch=$(uname -m)
if [ $arch = "arm64" ]; then
  arch="aarch64"
fi

builder_dockerfile=$(cat <<'EOF'
FROM alpine:3.20
RUN apk add --no-cache make gcc musl-dev autoconf automake git wget
RUN apk add --no-cache zlib-dev zlib-static libressl-dev
# below required for sys/mman.h
RUN apk add --no-cache linux-headers
EOF
)

build_script=$(cat <<'EOF'
#! /bin/sh
set -e

git clone -c advice.detachedHead=false --depth=1 \
  --branch "V_9_8_P1" \
  https://github.com/openssh/openssh-portable \
  openssh-portable
cd openssh-portable
autoreconf
./configure --prefix=/usr --enable-static --with-ldflags=-static

sed -i 's/^# \?define SFTP_MAX_MSG_LENGTH[ \t]*.*/#define SFTP_MAX_MSG_LENGTH 5242880/g' sftp-common.h

make -j$(nproc) sftp-server
cp sftp-server /workspace/sftp-server.$X_ARCH.bin
EOF
)

SCRIPT_DIR=$(cd `dirname "${BASH_SOURCE[0]}"` && pwd)
temp_dir=$(mktemp -d -t sftpserver-build.XXXXX)
echo "Using temp directory: $temp_dir"
echo "$build_script" > "$temp_dir/build.sh"
chmod +x $temp_dir/*.sh
echo -e "$builder_dockerfile" > "$SCRIPT_DIR/sftpserver-builder.dockerfile"

docker build -t sftpserver-builder -f $SCRIPT_DIR/sftpserver-builder.dockerfile $SCRIPT_DIR

docker run --rm -it \
    -e X_ARCH=$arch \
    -u $(id -u):$(id -g) \
    -w /workspace \
    -v $temp_dir:/workspace \
    sftpserver-builder \
    /workspace/build.sh

cp $temp_dir/sftp-server.*.bin $SCRIPT_DIR/../../src/ai/backend/runner
ls -lh src/ai/backend/runner

cd $SCRIPT_DIR/..
rm -rf "$temp_dir"
