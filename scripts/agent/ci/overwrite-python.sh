#! /bin/bash
set -ev

PYTHON_MAJOR=$(echo "$PYTHON_VERSION" | awk -F \. '{print $1}')
docker create --name pybin python:$PYTHON_VERSION
sudo docker cp "pybin:/usr/local/bin" /usr/local
sudo docker cp "pybin:/usr/local/lib/python${PYTHON_VERSION}" "/usr/local/lib/python${PYTHON_VERSION}"
sudo docker cp "pybin:/usr/local/lib/libpython${PYTHON_VERSION}m.so" /usr/local/lib
sudo docker cp "pybin:/usr/local/lib/libpython${PYTHON_VERSION}m.so.1.0" /usr/local/lib
sudo docker cp "pybin:/usr/local/lib/libpython${PYTHON_MAJOR}.so" /usr/local/lib
sudo docker cp "pybin:/usr/local/include/python${PYTHON_VERSION}m" /usr/local/include
docker rm pybin
sudo ldconfig
rm -rf ~/virtualenv/python*
python --version
