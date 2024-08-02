#! /bin/bash
set -e

arch=$(uname -m)
distros=("alpine3.8" "centos8.0" "ubuntu18.04" "ubuntu20.04" "ubuntu22.04")

ubuntu1804_builder_dockerfile=$(cat <<'EOF'
FROM ubuntu:18.04
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update
RUN apt-get install -y make gcc
RUN apt-get install -y autoconf automake zlib1g-dev libtool shtool pkg-config
RUN mkdir -p /opt && ln -s /usr/bin/shtool /opt/
EOF
)
ubuntu2004_builder_dockerfile=$(cat <<'EOF'
FROM ubuntu:20.04
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update
RUN apt-get install -y make gcc
RUN apt-get install -y autoconf automake zlib1g-dev libtool shtool pkg-config
RUN mkdir -p /opt && ln -s /usr/bin/shtool /opt/
EOF
)
ubuntu2204_builder_dockerfile=$(cat <<'EOF'
FROM ubuntu:22.04
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update
RUN apt-get install -y make gcc
RUN apt-get install -y autoconf automake zlib1g-dev libtool shtool pkg-config
RUN mkdir -p /opt && ln -s /usr/bin/shtool /opt/
EOF
)
alpine_builder_dockerfile=$(cat <<'EOF'
FROM alpine:3.8
RUN apk add --no-cache make gcc musl-dev
RUN apk add --no-cache autoconf automake zlib-dev libtool pkgconfig
RUN wget https://ftp.gnu.org/gnu/shtool/shtool-2.0.8.tar.gz \
    && tar -xzf shtool-2.0.8.tar.gz \
    && cd shtool-2.0.8 \
    && ./configure && make && make install
RUN mkdir -p /opt && ln -s /usr/local/bin/shtool /opt/
EOF
)
centos8_builder_dockerfile=$(cat <<'EOF'
FROM centos:centos8
RUN sed -i 's|#baseurl=http://mirror.centos.org|baseurl=http://vault.centos.org|g' /etc/yum.repos.d/CentOS-Linux-*

RUN dnf install -y make gcc
RUN dnf install -y automake autoconf libtool dnf-plugins-core pkg-config
RUN dnf config-manager --set-enabled powertools
RUN dnf install -y zlib-static glibc-static libxcrypt-static wget
RUN wget https://ftp.gnu.org/gnu/shtool/shtool-2.0.8.tar.gz \
    && tar -xzf shtool-2.0.8.tar.gz \
    && cd shtool-2.0.8 \
    && ./configure && make && make install
RUN mkdir -p /opt && ln -s /usr/local/bin/shtool /opt/
EOF
)


build_script=$(cat <<'EOF'
#! /bin/sh
set -e
cd "dropbear-${X_DISTRO}"
./configure --enable-static --prefix=/opt/kernel

# Improve SFTP up/download throughputs.
# FIXME: Temporarily falling back to the default to avoid PyCharm compatibility issue
sed -i 's/\(DEFAULT_RECV_WINDOW\) [0-9][0-9]*/\1 2097152/' src/default_options.h
sed -i 's/\(RECV_MAX_PAYLOAD_LEN\) [0-9][0-9]*/\1 2621440/' src/default_options.h
sed -i 's/\(TRANS_MAX_PAYLOAD_LEN\) [0-9][0-9]*/\1 2621440/' src/default_options.h
sed -i 's/\(MAX_CMD_LEN\) [0-9][0-9]*/\1 20000/' src/sysoptions.h
sed -i '/channel->transwindow -= len;/s/^/\/\//' src/common-channel.c
sed -i 's/DEFAULT_PATH/getenv("PATH")/' src/svr-chansession.c

# Disable clearing environment variables for new pty sessions and remote commands
sed -i 's%/\* *#define \+DEBUG_VALGRIND *\*/%#define DEBUG_VALGRIND%' src/debug.h

make
cp dropbear        ../dropbear.$X_DISTRO.$X_ARCH.bin
cp dropbearkey     ../dropbearkey.$X_DISTRO.$X_ARCH.bin
cp dropbearconvert ../dropbearconvert.$X_DISTRO.$X_ARCH.bin
make clean
EOF
)

DROPBEAR_TAG="DROPBEAR_2024.85"
SCRIPT_DIR=$(cd `dirname "${BASH_SOURCE[0]}"` && pwd)
temp_dir=$(mktemp -d -t dropbear-build.XXXXX)
echo "Using temp directory: $temp_dir"
echo "$build_script" > "$temp_dir/build.sh"
chmod +x $temp_dir/*.sh
echo "$ubuntu1804_builder_dockerfile" > "$SCRIPT_DIR/dropbear-builder.ubuntu18.04.dockerfile"
echo "$ubuntu2004_builder_dockerfile" > "$SCRIPT_DIR/dropbear-builder.ubuntu20.04.dockerfile"
echo "$ubuntu2204_builder_dockerfile" > "$SCRIPT_DIR/dropbear-builder.ubuntu22.04.dockerfile"
echo "$alpine_builder_dockerfile" > "$SCRIPT_DIR/dropbear-builder.alpine3.8.dockerfile"
echo "$centos8_builder_dockerfile" > "$SCRIPT_DIR/dropbear-builder.centos8.0.dockerfile"

for distro in "${distros[@]}"; do
  docker build -t dropbear-builder:$distro \
    -f $SCRIPT_DIR/dropbear-builder.$distro.dockerfile $SCRIPT_DIR
done
cd "${temp_dir}"
git clone -c advice.detachedHead=false --branch "$DROPBEAR_TAG" --depth=1 https://github.com/mkj/dropbear ./dropbear
for distro in "${distros[@]}"; do
  # Perform a local clone for a clean build
  git clone -c advice.detachedHead=false --branch "$DROPBEAR_TAG" --depth=1 ./dropbear "./dropbear-${distro}"
  docker run --rm -it \
    -e X_DISTRO=$distro \
    -e X_ARCH=$arch \
    -u $(id -u):$(id -g) \
    -w /workspace \
    -v "${temp_dir}:/workspace" \
    "dropbear-builder:${distro}" \
    /workspace/build.sh
done

ls -l .
cp dropbear.*.bin        $SCRIPT_DIR/../../src/ai/backend/runner
cp dropbearkey.*.bin     $SCRIPT_DIR/../../src/ai/backend/runner
cp dropbearconvert.*.bin $SCRIPT_DIR/../../src/ai/backend/runner

rm -rf "$temp_dir"
