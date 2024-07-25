#! /bin/bash
set -e

arch=$(uname -m)

if [ $arch = "arm64" ]; then
  arch="aarch64"
fi

builder_dockerfile=$(cat <<'EOF'
FROM alpine:3.8
RUN apk add --no-cache make gcc musl-dev git
RUN apk add --no-cache autoconf automake libtool
RUN apk add --no-cache wget
# below required for sys/mman.h
RUN apk add --no-cache linux-headers
EOF
)

build_script=$(cat <<'EOF'
#! /bin/sh
set -e
export ZLIB_VER=1.3.1
export SSL_VER=1.1.1i

cd /workspace

wget https://www.zlib.net/zlib-${ZLIB_VER}.tar.gz -O /workspace/zlib-${ZLIB_VER}.tar.gz && \
    wget https://www.openssl.org/source/openssl-${SSL_VER}.tar.gz -O /workspace/openssl-${SSL_VER}.tar.gz
git clone -c advice.detachedHead=false --branch "V_8_9_P1" https://github.com/openssh/openssh-portable openssh-portable

tar xzvf zlib-${ZLIB_VER}.tar.gz && \
    tar xzvf openssl-${SSL_VER}.tar.gz

echo "BUILD: zlib" && \
    cd /workspace/zlib-${ZLIB_VER} && \
    ./configure --prefix=/workspace/usr --static && \
    make -j$(nproc) && \
    make install

echo "BUILD: OpenSSL" && \
    cd /workspace/openssl-${SSL_VER} && \
    ./config --prefix=/workspace/usr no-shared --openssldir=/workspace/usr/openssl && \
    make -j$(nproc) && \
    make install_sw

cd /workspace/openssh-portable
autoreconf
export LDFLAGS="-L/workspace/usr/lib -pthread -static"
export CFLAGS="-I/workspace/usr/include -L/workspace/usr/lib -fPIC -static"
export CPPFLAGS="-I/workspace/usr/include -L/workspace/usr/lib -fPIC -static"
export LIBS="-ldl"
./configure --prefix=/workspace/usr
sed -i 's/^# \?define SFTP_MAX_MSG_LENGTH[ \t]*.*/#define SFTP_MAX_MSG_LENGTH 5242880/g' sftp-common.h
make -j$(nproc) sftp-server scp
cp sftp-server /workspace/sftp-server.$X_ARCH.bin
cp scp /workspace/scp.$X_ARCH.bin
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

ls -l .
cp $temp_dir/sftp-server.*.bin $SCRIPT_DIR/../../src/ai/backend/runner
cp $temp_dir/scp.*.bin $SCRIPT_DIR/../../src/ai/backend/runner

cd $SCRIPT_DIR/..
rm -rf "$temp_dir"
