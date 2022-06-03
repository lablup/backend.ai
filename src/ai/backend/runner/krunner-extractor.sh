#! /bin/sh
rm -rf /root/volume/*
tar xJf /root/archive.tar.xz -C /root/volume/
echo "$KRUNNER_VERSION" > /root/volume/VERSION
