FROM alpine:3.18
RUN apk add --no-cache make gcc musl-dev
RUN apk add --no-cache autoconf automake zlib-dev libtool shtool
