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
