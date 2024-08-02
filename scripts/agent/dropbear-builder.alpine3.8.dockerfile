FROM alpine:3.8
RUN apk add --no-cache make gcc musl-dev
RUN apk add --no-cache autoconf automake zlib-dev libtool pkgconfig
RUN wget https://ftp.gnu.org/gnu/shtool/shtool-2.0.8.tar.gz \
    && tar -xzf shtool-2.0.8.tar.gz \
    && cd shtool-2.0.8 \
    && ./configure && make && make install
RUN mkdir -p /opt && ln -s /usr/local/bin/shtool /opt/
