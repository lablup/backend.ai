#! /bin/bash
set -e

arch=$(uname -m)
if [ $arch = "arm64" ]; then
  arch="aarch64"
fi

builder_dockerfile=$(cat <<'EOF'
FROM alpine:3.20
RUN apk add --no-cache make gcc g++ musl-dev
RUN apk add --no-cache file bison flex curl
RUN apk add --no-cache pkgconfig
EOF
)

build_script=$(cat <<'EOF'
#! /bin/sh
set -e
TARGETDIR=$PWD/build
mkdir -p $TARGETDIR

curl -LO https://github.com/libevent/libevent/releases/download/release-2.0.22-stable/libevent-2.0.22-stable.tar.gz
tar -zxvf libevent-2.0.22-stable.tar.gz
curl -LO https://ftp.kaist.ac.kr/gnu/ncurses/ncurses-6.4.tar.gz
tar zxvf ncurses-6.4.tar.gz
curl -LO https://github.com/tmux/tmux/releases/download/3.4/tmux-3.4.tar.gz
tar zxvf tmux-3.4.tar.gz

cd libevent-2.0.22-stable
./configure --prefix=$TARGETDIR --disable-openssl --enable-shared=no --enable-static=yes --with-pic && make -j$(nproc) && make install
make clean
cd ..
cd ncurses-6.4

CPPFLAGS="-P" ./configure --prefix $TARGETDIR \
            --with-default-terminfo-dir=/usr/share/terminfo \
            --with-terminfo-dirs="/etc/terminfo:/lib/terminfo:/usr/share/terminfo" \
            --enable-pc-files \
            --with-pkg-config-libdir=$TARGETDIR/lib/pkgconfig \
&& make -j$(nproc) && make install.progs && make install.includes && make install.libs
make clean
cd ..
cd tmux-3.4
PKG_CONFIG_PATH=$TARGETDIR/lib/pkgconfig \
    CFLAGS="-I$TARGETDIR/include/event2 -I$TARGETDIR/include/ncurses" \
    LDFLAGS="-L$TARGETDIR/lib" \
    ./configure --enable-static --prefix=$TARGETDIR && make -j$(nproc)
cp tmux ../tmux.$X_ARCH.bin

EOF
)

SCRIPT_DIR=$(cd `dirname "${BASH_SOURCE[0]}"` && pwd)
temp_dir=$(mktemp -d -t tmux-build.XXXXX)
echo "Using temp directory: $temp_dir"
echo "$build_script" > "$temp_dir/build.sh"
chmod +x $temp_dir/*.sh
echo "$builder_dockerfile" > "$SCRIPT_DIR/tmux-builder.dockerfile"

docker build -t tmux-builder \
  -f $SCRIPT_DIR/tmux-builder.dockerfile $SCRIPT_DIR

docker run --rm -it \
  -e X_ARCH=$arch \
  -w /workspace \
  -v $temp_dir:/workspace \
  -u $(id -u):$(id -g) \
  tmux-builder \
  /workspace/build.sh

cp $temp_dir/tmux.*.bin        $SCRIPT_DIR/../../src/ai/backend/runner
ls -lh src/ai/backend/runner

rm -rf "$temp_dir"
