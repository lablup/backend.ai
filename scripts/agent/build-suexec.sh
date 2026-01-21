#! /bin/bash
set -e

arch=$(uname -m)
if [ $arch = "arm64" ]; then
  arch="aarch64"
fi

builder_dockerfile=$(cat <<'EOF'
FROM alpine:3.20
RUN apk add --no-cache make gcc musl-dev git
EOF
)

build_script=$(cat <<'EOF'
#! /bin/sh
set -e
gcc -o su-exec.$X_ARCH.bin su-exec.c -static
EOF
)

SCRIPT_DIR=$(cd `dirname "${BASH_SOURCE[0]}"` && pwd)
temp_dir=$(mktemp -d -t suexec-build.XXXXX)
echo "Using temp directory: $temp_dir"
echo "$build_script" > "$temp_dir/build.sh"
chmod +x $temp_dir/*.sh
echo "$builder_dockerfile" > "$SCRIPT_DIR/suexec-builder.dockerfile"

docker build -t suexec-builder \
  -f $SCRIPT_DIR/suexec-builder.dockerfile $SCRIPT_DIR

cp $SCRIPT_DIR/su-exec.c $temp_dir

docker run --rm -it \
  -e X_ARCH=$arch \
  -u $(id -u):$(id -g) \
  -w /workspace \
  -v $temp_dir:/workspace \
  suexec-builder \
  /workspace/build.sh

cp $temp_dir/su-exec.*.bin $SCRIPT_DIR/../../src/ai/backend/runner
ls -lh src/ai/backend/runner

rm -rf "$temp_dir"
