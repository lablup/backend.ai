#! /bin/bash
set -e

arch=$(uname -m)
distros=("glibc" "musl")

glibc_builder_dockerfile=$(cat <<'EOF'
FROM ubuntu:20.04
RUN apt-get update
RUN apt-get install -y make gcc
RUN apt-get install -y autoconf automake zlib1g-dev
EOF
)

musl_builder_dockerfile=$(cat <<'EOF'
FROM alpine:3.8
RUN apk add --no-cache make gcc musl-dev
RUN apk add --no-cache autoconf automake zlib-dev
EOF
)

build_script=$(cat <<'EOF'
#! /bin/sh
set -e
cd dropbear
autoreconf
./configure --enable-static --prefix=/opt/kernel

# Improve SFTP up/download throughputs.
# FIXME: Temporarily falling back to the default to avoid PyCharm compatibility issue
sed -i 's/\(DEFAULT_RECV_WINDOW\) [0-9][0-9]*/\1 2097152/' default_options.h
sed -i 's/\(RECV_MAX_PAYLOAD_LEN\) [0-9][0-9]*/\1 2621440/' default_options.h
sed -i 's/\(TRANS_MAX_PAYLOAD_LEN\) [0-9][0-9]*/\1 2621440/' default_options.h
sed -i 's/DEFAULT_PATH/getenv("PATH")/' svr-chansession.c

# Disable clearing environment variables for new pty sessions and remote commands
sed -i 's%/\* *#define \+DEBUG_VALGRIND *\*/%#define DEBUG_VALGRIND%' debug.h

make
cp dropbear        ../dropbear.$X_DISTRO.$X_ARCH.bin
cp dropbearkey     ../dropbearkey.$X_DISTRO.$X_ARCH.bin
cp dropbearconvert ../dropbearconvert.$X_DISTRO.$X_ARCH.bin
make clean
EOF
)

SCRIPT_DIR=$(cd `dirname "${BASH_SOURCE[0]}"` && pwd)
temp_dir=$(mktemp -d -t dropbear-build.XXXXX)
echo "Using temp directory: $temp_dir"
echo "$build_script" > "$temp_dir/build.sh"
chmod +x $temp_dir/*.sh
echo "$glibc_builder_dockerfile" > "$SCRIPT_DIR/dropbear-builder.glibc.dockerfile"
echo "$musl_builder_dockerfile" > "$SCRIPT_DIR/dropbear-builder.musl.dockerfile"

for distro in "${distros[@]}"; do
  docker build -t dropbear-builder:$distro \
    -f $SCRIPT_DIR/dropbear-builder.$distro.dockerfile $SCRIPT_DIR
done

cd "$temp_dir"
git clone -c advice.detachedHead=false --branch "DROPBEAR_2020.81" https://github.com/mkj/dropbear dropbear

for distro in "${distros[@]}"; do
  docker run --rm -it \
    -e X_DISTRO=$distro \
    -e X_ARCH=$arch \
    -u $(id -u):$(id -g) \
    -w /workspace \
    -v $temp_dir:/workspace \
    dropbear-builder:$distro \
    /workspace/build.sh
done

ls -l .
cp dropbear.*.bin        $SCRIPT_DIR/../src/ai/backend/runner
cp dropbearkey.*.bin     $SCRIPT_DIR/../src/ai/backend/runner
cp dropbearconvert.*.bin $SCRIPT_DIR/../src/ai/backend/runner

rm -rf "$temp_dir"
