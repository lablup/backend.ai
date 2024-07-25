#! /bin/bash
set -e

arch=$(uname -m)

if [ $arch = "arm64" ]; then
  arch="aarch64"
fi

builder_dockerfile=$(cat <<'EOF'
FROM alpine:3.8
RUN apk add --no-cache make gcc musl-dev
RUN apk add --no-cache autoconf automake libtool zlib-dev git
EOF
)


build_script=$(cat <<'EOF'
#! /bin/sh
set -e

git clone -c advice.detachedHead=false --branch "DROPBEAR_2024.85" https://github.com/mkj/dropbear dropbear

cd dropbear
autoconf && autoheader
./configure --enable-static --prefix=/opt/kernel

# Improve SFTP up/download throughputs.
sed -i 's/\(DEFAULT_RECV_WINDOW\) [0-9][0-9]*/\1 2097152/' default_options.h
sed -i 's/\(RECV_MAX_PAYLOAD_LEN\) [0-9][0-9]*/\1 2621440/' default_options.h
sed -i 's/\(TRANS_MAX_PAYLOAD_LEN\) [0-9][0-9]*/\1 2621440/' default_options.h
sed -i 's/\(MAX_CMD_LEN\) [0-9][0-9]*/\1 20000/' sysoptions.h
sed -i '/channel->transwindow -= len;/s/^/\/\//' common-channel.c
sed -i 's/DEFAULT_PATH/getenv("PATH")/' svr-chansession.c

# Disable clearing environment variables for new pty sessions and remote commands
sed -i 's%/\* *#define \+DEBUG_VALGRIND *\*/%#define DEBUG_VALGRIND%' src/debug.h

make -j$(nproc)
cp dropbear        ../dropbear.$X_ARCH.bin
cp dropbearkey     ../dropbearkey.$X_ARCH.bin
cp dropbearconvert ../dropbearconvert.$X_ARCH.bin
make clean
EOF
)

SCRIPT_DIR=$(cd `dirname "${BASH_SOURCE[0]}"` && pwd)
temp_dir=$(mktemp -d -t dropbear-build.XXXXX)
echo "Using temp directory: $temp_dir"
echo "$build_script" > "$temp_dir/build.sh"
chmod +x $temp_dir/*.sh
echo "$builder_dockerfile" > "$SCRIPT_DIR/dropbear-builder.dockerfile"

docker build -t dropbear-builder \
  -f $SCRIPT_DIR/dropbear-builder.dockerfile $SCRIPT_DIR

docker run --rm -it \
  -e X_ARCH=$arch \
  -u $(id -u):$(id -g) \
  -w /workspace \
  -v $temp_dir:/workspace \
  dropbear-builder \
  /workspace/build.sh

ls -l .
cp $temp_dir/dropbear.*.bin        $SCRIPT_DIR/../../src/ai/backend/runner
cp $temp_dir/dropbearkey.*.bin     $SCRIPT_DIR/../../src/ai/backend/runner
cp $temp_dir/dropbearconvert.*.bin $SCRIPT_DIR/../../src/ai/backend/runner

rm -rf "$temp_dir"
