#! /bin/bash
set -e

arch=$(uname -m)
distros=("glibc" "musl")

glibc_builder_dockerfile=$(cat <<'EOF'
FROM ubuntu:20.04
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update
RUN apt-get install -y make gcc g++ bison flex
RUN apt-get install -y pkg-config
EOF
)

musl_builder_dockerfile=$(cat <<'EOF'
FROM alpine:3.8
RUN apk add --no-cache make gcc g++ musl-dev file bison flex
RUN apk add --no-cache pkgconfig
EOF
)

build_script=$(cat <<'EOF'
#! /bin/sh
set -e
TARGETDIR=$PWD/build
mkdir -p $TARGETDIR

cd libevent-2.0.22-stable
./configure --prefix=$TARGETDIR --disable-openssl --enable-shared=no --enable-static=yes --with-pic && make && make install
make clean
cd ..
cd ncurses-6.0

CPPFLAGS="-P" ./configure --prefix $TARGETDIR \
            --with-default-terminfo-dir=/usr/share/terminfo \
            --with-terminfo-dirs="/etc/terminfo:/lib/terminfo:/usr/share/terminfo" \
            --enable-pc-files \
            --with-pkg-config-libdir=$TARGETDIR/lib/pkgconfig \
&& make && make install
make clean
cd ..
cd tmux-3.0a
PKG_CONFIG_PATH=$TARGETDIR/lib/pkgconfig \
    CFLAGS="-I$TARGETDIR/include/event2 -I$TARGETDIR/include/ncurses" \
    LDFLAGS="-L$TARGETDIR/lib" \
    ./configure --enable-static --prefix=$TARGETDIR && make && make install
make clean
cd ..

cp $TARGETDIR/bin/tmux tmux.$X_DISTRO.$X_ARCH.bin
rm -rf $TARGETDIR

EOF
)

SCRIPT_DIR=$(cd `dirname "${BASH_SOURCE[0]}"` && pwd)
temp_dir=$(mktemp -d -t tmux-build.XXXXX)
echo "Using temp directory: $temp_dir"
echo "$build_script" > "$temp_dir/build.sh"
chmod +x $temp_dir/*.sh
echo "$glibc_builder_dockerfile" > "$SCRIPT_DIR/tmux-builder.glibc.dockerfile"
echo "$musl_builder_dockerfile" > "$SCRIPT_DIR/tmux-builder.musl.dockerfile"

for distro in "${distros[@]}"; do
  docker build -t tmux-builder:$distro \
    -f $SCRIPT_DIR/tmux-builder.$distro.dockerfile $SCRIPT_DIR
done

cd "$temp_dir"

curl -LO https://github.com/libevent/libevent/releases/download/release-2.0.22-stable/libevent-2.0.22-stable.tar.gz
tar -zxvf libevent-2.0.22-stable.tar.gz
curl -LO https://mirror.yongbok.net/gnu/ncurses/ncurses-6.0.tar.gz
tar zxvf ncurses-6.0.tar.gz
curl -LO https://github.com/tmux/tmux/releases/download/3.0a/tmux-3.0a.tar.gz
tar zxvf tmux-3.0a.tar.gz

for distro in "${distros[@]}"; do
  docker run --rm -it \
    -e X_DISTRO=$distro \
    -e X_ARCH=$arch \
    -w /workspace \
    -v $temp_dir:/workspace \
    tmux-builder:$distro \
    /workspace/build.sh
done

ls -l .
cp tmux.*.bin        $SCRIPT_DIR/../src/ai/backend/runner

rm -rf "$temp_dir"
