FROM ubuntu:noble
RUN apt-get update && apt-get install -y --no-install-recommends \
    debootstrap erofs-utils cryptsetup-bin systemd-ukify systemd-boot-efi \
    dosfstools mtools e2fsprogs gdisk mount util-linux curl ca-certificates python3 xz-utils \
    && rm -rf /var/lib/apt/lists/*
RUN printf '#!/bin/sh\nexec /usr/bin/wget --tries=20 --waitretry=2 --retry-on-http-error=503 "$@"\n' \
    > /usr/local/bin/wget && chmod 0755 /usr/local/bin/wget
