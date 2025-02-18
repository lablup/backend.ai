#! /bin/bash
set -e

# Set default versions
: "${LIBEVENT_VERSION:=2.1.12}"
: "${NCURSES_VERSION:=6.5}"
: "${TMUX_VERSION:=3.5a}"

# Architecture handling
if [ -z "$ARCH" ]; then
    host_arch=$(uname -m)
    case "$host_arch" in
        "x86_64")
            ARCH="amd64"
            ;;
        "arm64" | "aarch64")
            ARCH="arm64"
            ;;
        *)
            echo "Unsupported architecture: $host_arch"
            exit 1
            ;;
    esac
else
    case "$ARCH" in
        "amd64" | "arm64")
            # Valid architecture specified
            ;;
        *)
            echo "Invalid architecture specified: $ARCH. Must be either 'amd64' or 'arm64'"
            exit 1
            ;;
    esac
fi

# Convert ARCH to Docker platform argument
case "$ARCH" in
    "amd64")
        DOCKER_PLATFORM="linux/amd64"
        LIBEVENT_ARCH="x86_64"
        ;;
    "arm64")
        DOCKER_PLATFORM="linux/arm64"
        LIBEVENT_ARCH="aarch64"
        ;;
esac

builder_dockerfile=$(cat <<'EOF'
FROM alpine:3.21
RUN apk add --no-cache make gcc g++ musl-dev
RUN apk add --no-cache file bison flex curl
RUN apk add --no-cache pkgconfig
RUN apk add --no-cache python3
EOF
)

build_script=$(cat <<EOF
#! /bin/sh
set -e
TARGETDIR=\$PWD/build
mkdir -p \$TARGETDIR

curl -LO https://github.com/libevent/libevent/releases/download/release-${LIBEVENT_VERSION}-stable/libevent-${LIBEVENT_VERSION}-stable.tar.gz
tar -zxvf libevent-${LIBEVENT_VERSION}-stable.tar.gz
curl -LO https://ftp.kaist.ac.kr/gnu/ncurses/ncurses-${NCURSES_VERSION}.tar.gz
tar zxvf ncurses-${NCURSES_VERSION}.tar.gz
curl -LO https://github.com/tmux/tmux/releases/download/${TMUX_VERSION}/tmux-${TMUX_VERSION}.tar.gz
tar zxvf tmux-${TMUX_VERSION}.tar.gz

cd libevent-${LIBEVENT_VERSION}-stable
./configure --prefix=\$TARGETDIR --disable-openssl --enable-shared=no --enable-static=yes --with-pic && make -j\$(nproc) && make install
make clean
cd ..
cd ncurses-${NCURSES_VERSION}

CPPFLAGS="-P" ./configure --prefix=\$TARGETDIR \\
            --with-default-terminfo-dir=/usr/share/terminfo \\
            --with-terminfo-dirs="/etc/terminfo:/lib/terminfo:/usr/share/terminfo" \\
            --enable-pc-files \\
            --with-pkg-config-libdir=\$TARGETDIR/lib/pkgconfig \\
&& make -j\$(nproc) && make install.progs && make install.includes && make install.libs
make clean
cd ..
cd tmux-${TMUX_VERSION}
PKG_CONFIG_PATH=\$TARGETDIR/lib/pkgconfig \\
    CFLAGS="-I\$TARGETDIR/include/event2 -I\$TARGETDIR/include/ncurses" \\
    LDFLAGS="-L\$TARGETDIR/lib" \\
    ./configure --enable-static --prefix=\$TARGETDIR && make -j\$(nproc)
cp tmux ../tmux.\$X_ARCH.bin

EOF
)

SCRIPT_DIR=$(cd `dirname "${BASH_SOURCE[0]}"` && pwd)
temp_dir=$(mktemp -d -t tmux-build.XXXXX)
echo "Using temp directory: $temp_dir"
echo "$build_script" > "$temp_dir/build.sh"
chmod +x $temp_dir/*.sh
echo "$builder_dockerfile" > "$SCRIPT_DIR/tmux-builder.dockerfile"

docker build --load --platform $DOCKER_PLATFORM -t tmux-builder:$ARCH \
  -f $SCRIPT_DIR/tmux-builder.dockerfile $SCRIPT_DIR

docker run --rm -it \
  --platform $DOCKER_PLATFORM \
  -e ARCH=$ARCH \
  -e LIBEVENT_VERSION=$LIBEVENT_VERSION \
  -e NCURSES_VERSION=$NCURSES_VERSION \
  -e TMUX_VERSION=$TMUX_VERSION \
  -w /workspace \
  -v $temp_dir:/workspace \
  -u $(id -u):$(id -g) \
  tmux-builder:$ARCH \
  /workspace/build.sh

cp $temp_dir/tmux.*.bin $SCRIPT_DIR/../../src/ai/backend/runner
ls -lh $SCRIPT_DIR/../../src/ai/backend/runner

rm -rf "$temp_dir"