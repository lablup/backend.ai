#! /bin/bash
set -e

arch=$(uname -m)
distros=("ubuntu16.04" "ubuntu18.04" "ubuntu20.04" "centos7.6" "alpine3.8")

ubuntu1604_builder_dockerfile=$(cat <<'EOF'
FROM ubuntu:16.04
RUN apt-get update
RUN apt-get install -y make gcc
EOF
)

ubuntu1804_builder_dockerfile=$(cat <<'EOF'
FROM ubuntu:18.04
RUN apt-get update
RUN apt-get install -y make gcc
EOF
)

ubuntu2004_builder_dockerfile=$(cat <<'EOF'
FROM ubuntu:20.04
RUN apt-get update
RUN apt-get install -y make gcc
EOF
)

centos_builder_dockerfile=$(cat <<'EOF'
FROM centos:7
RUN yum install -y make gcc
EOF
)

alpine_builder_dockerfile=$(cat <<'EOF'
FROM alpine:3.8
RUN apk add --no-cache make gcc musl-dev
EOF
)

build_script=$(cat <<'EOF'
#! /bin/sh
set -e
cd su-exec
make
cp su-exec ../su-exec.$X_DISTRO.$X_ARCH.bin
make clean
EOF
)

SCRIPT_DIR=$(cd `dirname "${BASH_SOURCE[0]}"` && pwd)
temp_dir=$(mktemp -d -t suexec-build.XXXXX)
echo "Using temp directory: $temp_dir"
echo "$build_script" > "$temp_dir/build.sh"
chmod +x $temp_dir/*.sh
echo "$ubuntu1604_builder_dockerfile" > "$SCRIPT_DIR/suexec-builder.ubuntu16.04.dockerfile"
echo "$ubuntu1804_builder_dockerfile" > "$SCRIPT_DIR/suexec-builder.ubuntu18.04.dockerfile"
echo "$ubuntu2004_builder_dockerfile" > "$SCRIPT_DIR/suexec-builder.ubuntu20.04.dockerfile"
echo "$centos_builder_dockerfile" > "$SCRIPT_DIR/suexec-builder.centos7.6.dockerfile"
echo "$alpine_builder_dockerfile" > "$SCRIPT_DIR/suexec-builder.alpine3.8.dockerfile"

for distro in "${distros[@]}"; do
  docker build -t suexec-builder:$distro \
    -f $SCRIPT_DIR/suexec-builder.$distro.dockerfile $SCRIPT_DIR
done

cd "$temp_dir"
git clone -c advice.detachedHead=false https://github.com/ncopa/su-exec su-exec

for distro in "${distros[@]}"; do
  docker run --rm -it \
    -e X_DISTRO=$distro \
    -e X_ARCH=$arch \
    -u $(id -u):$(id -g) \
    -w /workspace \
    -v $temp_dir:/workspace \
    suexec-builder:$distro \
    /workspace/build.sh
done

ls -l .
cp su-exec.*.bin $SCRIPT_DIR/../src/ai/backend/runner

rm -rf "$temp_dir"
