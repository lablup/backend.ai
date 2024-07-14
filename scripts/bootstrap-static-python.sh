#! /bin/bash

has_python() {
  "$1" -c '' >/dev/null 2>&1
  if [ "$?" -eq 0 ]; then
    echo 0  # ok
  else
    echo 1  # missing
  fi
}

install_static_python() {
  local build_date="20240713"
  local build_version="${STANDALONE_PYTHON_VERSION}"
  local build_tag="cpython-${build_version}+${build_date}-${STANDALONE_PYTHON_ARCH}-${STANDALONE_PYTHON_PLATFORM}"
  dist_url="https://github.com/indygreg/python-build-standalone/releases/download/${build_date}/${build_tag}-install_only.tar.gz"
  checksum_url="${dist_url}.sha256"
  cwd="$(pwd)"
  mkdir -p "${STANDALONE_PYTHON_PATH}"
  cd "${STANDALONE_PYTHON_PATH}"
  echo "Downloading and installing static Python (${build_tag}) for bootstrapping..."
  curl -o dist.tar.gz -L "$dist_url"
  echo "$(curl -sL $checksum_url) *dist.tar.gz" | shasum -a 256 --check --status
  if [ $? -ne 0 ]; then
    echo "Failed to validate the downloaded static build of Python binary!"
    exit 1
  fi
  tar xzf dist.tar.gz && rm dist.tar.gz
  mv python/* . && rmdir python
  cd "${cwd}"
}

STANDALONE_PYTHON_VERSION="3.12.4"
STANDALONE_PYTHON_ARCH=$(arch)
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    STANDALONE_PYTHON_PLATFORM="unknown-linux-gnu"
elif [[ "$OSTYPE" == "linux-musl"* ]]; then
    STANDALONE_PYTHON_PLATFORM="unknown-linux-musl"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    STANDALONE_PYTHON_PLATFORM="apple-darwin"
fi
export STANDALONE_PYTHON_PATH="$HOME/.cache/bai/bootstrap/cpython/${STANDALONE_PYTHON_VERSION}"
if [ "${STANDALONE_PYTHON_ARCH}" = "arm64" ]; then
  STANDALONE_PYTHON_ARCH="aarch64"
fi
export bpython="${STANDALONE_PYTHON_PATH}/bin/python3"
if [ $(has_python "$bpython") -ne 0 ]; then
  install_static_python
  $bpython -m ensurepip --upgrade
  $bpython -m pip --disable-pip-version-check install -q -U tomlkit
  $bpython -c 'import sys;print(sys.version_info)'
fi
