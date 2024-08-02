FROM ubuntu:20.04
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update
RUN apt-get install -y make gcc
RUN apt-get install -y autoconf automake zlib1g-dev libtool shtool pkg-config
RUN mkdir -p /opt && ln -s /usr/bin/shtool /opt/
