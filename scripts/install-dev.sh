#! /bin/bash

# Set "echo -e" as default
shopt -s xpg_echo

# For CentOS 7 or older versions of Linux only
# - To make old gcc to allow declaring a vairiable inside a for loop.
# PANTS_PYTHON_NATIVE_CODE_CPP_FLAGS="-std=gnu99"

RED="\033[0;91m"
GREEN="\033[0;92m"
YELLOW="\033[0;93m"
BLUE="\033[0;94m"
CYAN="\033[0;96m"
WHITE="\033[0;97m"
LRED="\033[1;31m"
LGREEN="\033[1;32m"
LYELLOW="\033[1;33m"
LBLUE="\033[1;34m"
LCYAN="\033[1;36m"
LWHITE="\033[1;37m"
LG="\033[0;37m"
NC="\033[0m"
REWRITELN="\033[A\r\033[K"

readlinkf() {
  $bpython -c "import os,sys; print(os.path.realpath(os.path.expanduser(sys.argv[1])))" "${1}"
}

sed_inplace() {
  # BSD sed and GNU sed implements the "-i" option differently.
  case "$OSTYPE" in
    darwin*) sed -i '' "$@" ;;
    bsd*) sed -i '' "$@" ;;
    *) sed -i "$@" ;;
  esac
}

trim() {
  echo "$1" | sed -e 's/^[[:space:]]*//g' -e 's/[[:space:]]*$//g'
}

usage() {
  echo "${GREEN}Backend.AI Development Setup${NC}: ${CYAN}Auto-installer Tool${NC}"
  echo ""
  echo "Installs the single-node development setup of Backend.AI from this"
  echo "semi-mono repository for the server-side components."
  echo ""
  echo "Changes in 22.06 or later:"
  echo ""
  echo "* Deprecated '-e/--env', '--install-path', '--python-version' options"
  echo "  as they are now deprecated because the working-copy directory"
  echo "  becomes the target installation path and identifies the"
  echo "  installation".
  echo "* '--server-branch' and '--client-branch' is now merged into a single"
  echo "  '--branch' option."
  echo ""
  echo "${LWHITE}USAGE${NC}"
  echo "  $0 ${LWHITE}[OPTIONS]${NC}"
  echo ""
  echo "${LWHITE}OPTIONS${NC}"
  echo "  ${LWHITE}-h, --help${NC}"
  echo "    Show this help message and exit"
  echo ""
  echo "  ${LWHITE}--enable-cuda${NC}"
  echo "    Install CUDA accelerator plugin and pull a"
  echo "    TenosrFlow CUDA kernel for testing/demo."
  echo "    (default: false)"
  echo ""
  echo "  ${LWHITE}--cuda-branch NAME${NC}"
  echo "    The branch of git clone for the CUDA accelerator "
  echo "    plugin; only valid if ${LWHITE}--enable-cuda${NC} is specified."
  echo "    If set as ${LWHITE}\"mock\"${NC}, it will install the mockup version "
  echo "    plugin so that you may develop and test CUDA integration "
  echo "    features without real GPUs."
  echo "    (default: main)"
  echo ""
  echo "  ${LWHITE}--postgres-port PORT${NC}"
  echo "    The port to bind the PostgreSQL container service."
  echo "    (default: 8100)"
  echo ""
  echo "  ${LWHITE}--redis-port PORT${NC}"
  echo "    The port to bind the Redis container service."
  echo "    (default: 8110)"
  echo ""
  echo "  ${LWHITE}--etcd-port PORT${NC}"
  echo "    The port to bind the etcd container service."
  echo "    (default: 8120)"
  echo ""
  echo "  ${LWHITE}--manager-port PORT${NC}"
  echo "    The port to expose the manager API service."
  echo "    (default: 8081)"
  echo ""
  echo "  ${LWHITE}--agent-rpc-port PORT${NC}"
  echo "    The port for the manager-to-agent RPC calls."
  echo "    (default: 6001)"
  echo ""
  echo "  ${LWHITE}--agent-watcher-port PORT${NC}"
  echo "    The port for the agent's watcher service."
  echo "    (default: 6009)"
}

show_error() {
  echo " "
  echo "${RED}[ERROR]${NC} ${LRED}$1${NC}"
}

show_warning() {
  echo " "
  echo "${YELLOW}[ERROR]${NC} ${LYELLOW}$1${NC}"
}

show_info() {
  echo " "
  echo "${BLUE}[INFO]${NC} ${GREEN}$1${NC}"
}

show_note() {
  echo " "
  echo "${BLUE}[NOTE]${NC} $1"
}

show_important_note() {
  echo " "
  echo "${LRED}[NOTE]${NC} $1"
}

has_python() {
  "$1" -c '' >/dev/null 2>&1
  if [ "$?" -eq 127 ]; then
    echo 0
  else
    echo 1
  fi
}

if [[ "$OSTYPE" == "linux-gnu" ]]; then
  if [ $(id -u) = "0" ]; then
    docker_sudo=''
  else
    docker_sudo='sudo'
  fi
else
  docker_sudo=''
fi
if [ $(id -u) = "0" ]; then
  sudo=''
else
  sudo='sudo'
fi

# Detect distribution
KNOWN_DISTRO="(Debian|Ubuntu|RedHat|CentOS|openSUSE|Amazon|Arista|SUSE)"
DISTRO=$(lsb_release -d 2>/dev/null | grep -Eo $KNOWN_DISTRO  || grep -Eo $KNOWN_DISTRO /etc/issue 2>/dev/null || uname -s)

if [ $DISTRO = "Darwin" ]; then
  DISTRO="Darwin"
elif [ -f /etc/debian_version -o "$DISTRO" == "Debian" -o "$DISTRO" == "Ubuntu" ]; then
  DISTRO="Debian"
elif [ -f /etc/redhat-release -o "$DISTRO" == "RedHat" -o "$DISTRO" == "CentOS" -o "$DISTRO" == "Amazon" ]; then
  DISTRO="RedHat"
elif [ -f /etc/system-release -o "$DISTRO" == "Amazon" ]; then
  DISTRO="RedHat"
else
  show_error "Sorry, your host OS distribution is not supported by this script."
  show_info "Please send us a pull request or file an issue to support your environment!"
  exit 1
fi
if [ $(has_python "python3") -eq 1 ]; then
  bpython=$(which "python3")
elif [ $(has_python "python") -eq 1 ]; then
  bpython=$(which "python")
elif [ $(has_python "python2") -eq 1 ]; then
  bpython=$(which "python2")
else
  # Ensure "readlinkf" is working...
  show_error "python (for bootstrapping) is not available!"
  show_info "This script assumes Python 2.7+/3+ is already available on your system."
  exit 1
fi

ROOT_PATH="$(pwd)"
if [ ! -f "${ROOT_PATH}/BUILD_ROOT" ]; then
  show_error "BUILD_ROOT is not found!"
  echo "You are not on the root directory of the repository checkout."
  echo "Please \`cd\` there and run \`./scripts/install-dev.sh <args>\`"
  exit 1
fi
PLUGIN_PATH="${ROOT_PATH}/plugins"
HALFSTACK_VOLUME_PATH="${ROOT_PATH}/volumes"
PANTS_VERSION=$(cat pants.toml | $bpython -c 'import sys,re;m=re.search("pants_version = \"([^\"]+)\"", sys.stdin.read());print(m.group(1) if m else sys.exit(1))')
PYTHON_VERSION=$(cat pants.toml | $bpython -c 'import sys,re;m=re.search("CPython==([^\"]+)", sys.stdin.read());print(m.group(1) if m else sys.exit(1))')
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
DOWNLOAD_BIG_IMAGES=0
ENABLE_CUDA=0
CUDA_BRANCH="main"
# POSTGRES_PORT="8100"
# REDIS_PORT="8110"
# ETCD_PORT="8120"
# MANAGER_PORT="8081"
# WEBSERVER_PORT="8080"
# AGENT_RPC_PORT="6001"
# AGENT_WATCHER_PORT="6009"
# VFOLDER_REL_PATH="vfroot/local"
# LOCAL_STORAGE_PROXY="local"
# LOCAL_STORAGE_VOLUME="volume1"

POSTGRES_PORT="8101"
REDIS_PORT="8111"
ETCD_PORT="8121"
MANAGER_PORT="8091"
WEBSERVER_PORT="8090"
AGENT_RPC_PORT="6011"
AGENT_WATCHER_PORT="6019"
VFOLDER_REL_PATH="vfroot/local"
LOCAL_STORAGE_PROXY="local"
# MUST be one of the real storage volumes
LOCAL_STORAGE_VOLUME="volume1"

while [ $# -gt 0 ]; do
  case $1 in
    -h | --help)           usage; exit 1 ;;
    --python-version)      PYTHON_VERSION=$2; shift ;;
    --python-version=*)    PYTHON_VERSION="${1#*=}" ;;
    --enable-cuda)         ENABLE_CUDA=1 ;;
    --download-big-images) DOWNLOAD_BIG_IMAGES=1 ;;
    --cuda-branch)         CUDA_BRANCH=$2; shift ;;
    --cuda-branch=*)       CUDA_BRANCH="${1#*=}" ;;
    --postgres-port)       POSTGRES_PORT=$2; shift ;;
    --postgres-port=*)     POSTGRES_PORT="${1#*=}" ;;
    --redis-port)          REDIS_PORT=$2; shift ;;
    --redis-port=*)        REDIS_PORT="${1#*=}" ;;
    --etcd-port)           ETCD_PORT=$2; shift ;;
    --etcd-port=*)         ETCD_PORT="${1#*=}" ;;
    --manager-port)         MANAGER_PORT=$2; shift ;;
    --manager-port=*)       MANAGER_PORT="${1#*=}" ;;
    --webserver-port)         WEBSERVER_PORT=$2; shift ;;
    --webserver-port=*)       WEBSERVER_PORT="${1#*=}" ;;
    --agent-rpc-port)       AGENT_RPC_PORT=$2; shift ;;
    --agent-rpc-port=*)     AGENT_RPC_PORT="${1#*=}" ;;
    --agent-watcher-port)   AGENT_WATCHER_PORT=$2; shift ;;
    --agent-watcher-port=*) AGENT_WATCHER_PORT="${1#*=}" ;;
    *)
      echo "Unknown option: $1"
      echo "Run '$0 --help' for usage."
      exit 1
  esac
  shift
done

install_brew() {
    case $DISTRO in
	Darwin)
	    if ! type "brew" > /dev/null 2>&1; then
	        show_info "try to support auto-install on macOS using Homebrew."
		/usr/bin/ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"
	    fi
    esac
}
install_script_deps() {
  case $DISTRO in
  Debian)
    $sudo apt-get update
    $sudo apt-get install -y git jq gcc make g++
    ;;
  RedHat)
    $sudo yum clean expire-cache  # next yum invocation will update package metadata cache
    $sudo yum install -y git jq gcc make gcc-c++
    ;;
  Darwin)
    if ! type "brew" >/dev/null 2>&1; then
      show_error "brew is not available!"
      show_info "Sorry, we only support auto-install on macOS using Homebrew. Please install it and try again."
      install_brew
    fi
    brew update
    brew install jq
    # Having Homebrew means that the user already has git.
    ;;
  esac
}

install_pybuild_deps() {
  case $DISTRO in
  Debian)
    $sudo apt-get install -y libssl-dev libreadline-dev libgdbm-dev zlib1g-dev libbz2-dev libsqlite3-dev libffi-dev liblzma-dev
    ;;
  RedHat)
    $sudo yum install -y openssl-devel readline-devel gdbm-devel zlib-devel bzip2-devel sqlite-devel libffi-devel xz-devel
    ;;
  Darwin)
    brew install openssl
    brew install readline
    brew install zlib xz
    brew install sqlite3 gdbm
    brew install tcl-tk
    if [ "$(uname -p)" = "arm" ]; then
      # On M1 Macs, psycopg2-binary tries to build itself and requires pg_config
      # to access the postgresql include/library path information.
      brew install postgresql
    fi
    ;;
  esac
}

install_git_lfs() {
  case $DISTRO in
  Debian)
    $sudo apt-get install -y git-lfs
    ;;
  RedHat)
    curl -s https://packagecloud.io/install/repositories/github/git-lfs/script.rpm.sh | $sudo bash
    $sudo yum install -y git-lfs
    ;;
  Darwin)
    brew install git-lfs
    ;;
  esac
  git lfs install
}

install_system_pkg() {
  # accepts three args: Debian-style name, RedHat-style name, and Homebrew-style name
  case $DISTRO in
  Debian)
    $sudo apt-get install -y $1
    ;;
  RedHat)
    $sudo yum install -y $2
    ;;
  Darwin)
    brew install $3
  esac
}

set_brew_python_build_flags() {
  local _prefix_openssl="$(brew --prefix openssl)"
  local _prefix_sqlite3="$(brew --prefix sqlite3)"
  local _prefix_readline="$(brew --prefix readline)"
  local _prefix_zlib="$(brew --prefix zlib)"
  local _prefix_gdbm="$(brew --prefix gdbm)"
  local _prefix_tcltk="$(brew --prefix tcl-tk)"
  local _prefix_xz="$(brew --prefix xz)"
  local _prefix_snappy="$(brew --prefix snappy)"
  local _prefix_libffi="$(brew --prefix libffi)"
  local _prefix_protobuf="$(brew --prefix protobuf)"
  export CFLAGS="-I${_prefix_openssl}/include -I${_prefix_sqlite3}/include -I${_prefix_readline}/include -I${_prefix_zlib}/include -I${_prefix_gdbm}/include -I${_prefix_tcltk}/include -I${_prefix_xz}/include -I${_prefix_snappy}/include -I${_prefix_libffi}/include -I${_prefix_protobuf}/include"
  export LDFLAGS="-L${_prefix_openssl}/lib -L${_prefix_sqlite3}/lib -L${_prefix_readline}/lib -L${_prefix_zlib}/lib -L${_prefix_gdbm}/lib -L${_prefix_tcltk}/lib -L${_prefix_xz}/lib -L${_prefix_snappy}/lib -L${_prefix_libffi}/lib -L${_prefix_protobuf}/lib"
}

install_python() {
  if [ -z "$(pyenv versions | grep -E "^\\*?[[:space:]]+${PYTHON_VERSION//./\\.}([[:blank:]]+.*)?$")" ]; then
    if [ "$DISTRO" = "Darwin" ]; then
      export PYTHON_CONFIGURE_OPTS="--enable-framework --with-tcl-tk"
      local _prefix_openssl="$(brew --prefix openssl)"
      local _prefix_sqlite3="$(brew --prefix sqlite3)"
      local _prefix_readline="$(brew --prefix readline)"
      local _prefix_zlib="$(brew --prefix zlib)"
      local _prefix_gdbm="$(brew --prefix gdbm)"
      local _prefix_tcltk="$(brew --prefix tcl-tk)"
      local _prefix_xz="$(brew --prefix xz)"
      export CFLAGS="-I${_prefix_openssl}/include -I${_prefix_sqlite3}/include -I${_prefix_readline}/include -I${_prefix_zlib}/include -I${_prefix_gdbm}/include -I${_prefix_tcltk}/include -I${_prefix_xz}/include"
      export LDFLAGS="-L${_prefix_openssl}/lib -L${_prefix_sqlite3}/lib -L${_prefix_readline}/lib -L${_prefix_zlib}/lib -L${_prefix_gdbm}/lib -L${_prefix_tcltk}/lib -L${_prefix_xz}/lib"
    fi
    pyenv install --skip-existing "${PYTHON_VERSION}"
    if [ $? -ne 0 ]; then
      show_error "Installing the Python version ${PYTHON_VERSION} via pyenv has failed."
      show_note "${PYTHON_VERSION} is not supported by your current installation of pyenv."
      show_note "Please update pyenv or lower PYTHON_VERSION in install-dev.sh script."
      exit 1
    fi
  else
    echo "${PYTHON_VERSION} is already installed."
  fi
}

install_git_hooks() {
  local magic_str="monorepo standard pre-commit hook"
  if [ -f .git/hooks/pre-commit ]; then
    grep -Fq "$magic_str" .git/hooks/pre-commit
    if [ $? -eq 0 ]; then
      :
    else
      echo "" >> .git/hooks/pre-commit
      cat scripts/pre-commit.sh >> .git/hooks/pre-commit
    fi
  else
    cp scripts/pre-commit.sh .git/hooks/pre-commit
    chmod +x .git/hooks/pre-commit
  fi
  local magic_str="monorepo standard pre-push hook"
  if [ -f .git/hooks/pre-push ]; then
    grep -Fq "$magic_str" .git/hooks/pre-push
    if [ $? -eq 0 ]; then
      :
    else
      echo "" >> .git/hooks/pre-push
      cat scripts/pre-push.sh >> .git/hooks/pre-push
    fi
  else
    cp scripts/pre-push.sh .git/hooks/pre-push
    chmod +x .git/hooks/pre-push
  fi
}

check_python() {
  pyenv shell "${PYTHON_VERSION}"
  local _pyprefix=$(python -c 'import sys; print(sys.prefix, end="")')
  python -c 'import ssl' > /dev/null 2>&1 /dev/null
  if [ $? -ne 0 ]; then
    show_error "Your Python (prefix: ${_pyprefix}) is missing SSL support. Please reinstall or rebuild it."
    exit 1
  else
    echo "SSL support: ok"
  fi
  python -c 'import lzma' > /dev/null 2>&1 /dev/null
  if [ $? -ne 0 ]; then
    show_error "Your Python (prefix: ${_pyprefix}) is missing LZMA (XZ) support. Please reinstall or rebuild it."
    exit 1
  else
    echo "LZMA support: ok"
  fi
  pyenv shell --unset
}

bootstrap_pants() {
  set -e
  mkdir -p .tmp
  if [ -f '.pants.env' -a -f './pants-local' ]; then
    echo "It seems that you have an already locally bootstrapped Pants."
    echo "The installer will keep using it."
    echo "If you want to reset it, delete ./.pants.env and ./pants-local files."
    ./pants-local version
    PANTS="./pants-local"
    return
  fi
  set +e
  PANTS="./pants"
  ./pants version
  # Note that Pants requires Python 3.9 (not Python 3.10!) to work properly.
  if [ $? -eq 1 ]; then
    show_info "Downloading and building Pants for the current setup"
    local _PYENV_PYVER=$(pyenv versions --bare | grep '^3\.9\.' | grep -v '/envs/' | sort -t. -k1,1r -k 2,2nr -k 3,3nr | head -n 1)
    if [ -z "$_PYENV_PYVER" ]; then
      echo "No Python 3.9 available via pyenv!"
      echo "Please install Python 3.9 using pyenv,"
      echo "or add 'PY=<python-executable-path>' in ./.pants.env to "
      echo "manually set the Pants-compatible interpreter path."
      exit 1
    else
      echo "Chosen Python $_PYENV_PYVER (from pyenv) as the local Pants interpreter"
    fi
    # In most cases, we won't need to modify the source code of pants.
    echo "ENABLE_PANTSD=true" > "$ROOT_PATH/.pants.env"
    echo "PY=\$(pyenv prefix $_PYENV_PYVER)/bin/python" >> "$ROOT_PATH/.pants.env"
    if [ -d tools/pants-src ]; then
      rm -rf tools/pants-src
    fi
    local PANTS_CLONE_VERSION="release_${PANTS_VERSION}"
    set -e
    git -c advice.detachedHead=false clone --branch=$PANTS_CLONE_VERSION --depth=1 https://github.com/pantsbuild/pants tools/pants-src
    # TODO: remove the manual patch after pants 2.13 or later is released.
    cd tools/pants-src
    local arch_name=$(uname -p)
    if [ "$arch_name" = "arm64" -o "$arch_name" = "aarch64" ] && [ "$DISTRO" != "Darwin" ]; then
      git apply ../pants-linux-aarch64.patch
    fi
    cd ../..
    ln -s tools/pants-local
    ./pants-local version
    PANTS="./pants-local"
  fi
  set +e
}

# BEGIN!

echo " "
echo "${LGREEN}Backend.AI one-line installer for developers${NC}"

# Check prerequisites
show_info "Checking prerequisites and script dependencies..."
install_script_deps
$bpython -m pip --disable-pip-version-check install -q requests requests-unixsocket
$bpython scripts/check-docker.py
if [ $? -ne 0 ]; then
  exit 1
fi
if [ "$DISTRO" = "Darwin" ]; then
  echo "validating Docker Desktop mount permissions..."
  docker pull alpine:3.8 > /dev/null
  docker run --rm -v "$HOME/.pyenv:/root/vol" alpine:3.8 ls /root/vol > /dev/null 2>&1
  if [ $? -ne 0 ]; then
    # backend.ai-krunner-DISTRO pkgs are installed in pyenv's virtualenv,
    # so ~/.pyenv must be mountable.
    show_error "You must allow mount of '$HOME/.pyenv' in the File Sharing preference of the Docker Desktop app."
    exit 1
  fi
  docker run --rm -v "$ROOT_PATH:/root/vol" alpine:3.8 ls /root/vol > /dev/null 2>&1
  if [ $? -ne 0 ]; then
    show_error "You must allow mount of '$ROOT_PATH' in the File Sharing preference of the Docker Desktop app."
    exit 1
  fi
  echo "${REWRITELN}validating Docker Desktop mount permissions: ok"
fi

# Install pyenv
read -r -d '' pyenv_init_script <<"EOS"
export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init --path)"
eval "$(pyenv init -)"
eval "$(pyenv virtualenv-init -)"
EOS
if ! type "pyenv" >/dev/null 2>&1; then
  # TODO: ask if install pyenv
  show_info "Installing pyenv..."
  set -e
  curl https://pyenv.run | sh
  for PROFILE_FILE in "zshrc" "bashrc" "profile" "bash_profile"
  do
    if [ -e "${HOME}/.${PROFILE_FILE}" ]
    then
      echo "$pyenv_init_script" >> "${HOME}/.${PROFILE_FILE}"
    fi
  done
  set +e
  eval "$pyenv_init_script"
  pyenv
else
  eval "$pyenv_init_script"
fi

# Install Python and pyenv virtualenvs
show_info "Checking and installing Python dependencies..."
install_pybuild_deps

show_info "Checking and installing git lfs support..."
install_git_lfs

show_info "Ensuring checkout of LFS files..."
git lfs pull

show_info "Configuring the standard git hooks..."
install_git_hooks

show_info "Installing Python..."
install_python

show_info "Checking Python features..."
check_python

show_info "Bootstrapping the Pants build system..."
bootstrap_pants

set -e

# Make directories
show_info "Using the current working-copy directory as the installation path..."

mkdir -p ./wheelhouse
if [ "$DISTRO" = "Darwin" -a "$(uname -p)" = "arm" ]; then
  show_info "Prebuild grpcio wheels for Apple Silicon..."
  if [ -z "$(pyenv virtualenvs | grep "tmp-grpcio-build")" ]; then
    pyenv virtualenv "${PYTHON_VERSION}" tmp-grpcio-build
  fi
  pyenv shell tmp-grpcio-build
  if [ $(python -c 'import sys; print(1 if sys.version_info >= (3, 10) else 0)') -eq 0 ]; then
    # ref: https://github.com/grpc/grpc/issues/25082
    export GRPC_PYTHON_BUILD_SYSTEM_OPENSSL=1
    export GRPC_PYTHON_BUILD_SYSTEM_ZLIB=1
    echo "Set grpcio wheel build variables."
  else
    unset GRPC_PYTHON_BUILD_SYSTEM_OPENSSL
    unset GRPC_PYTHON_BUILD_SYSTEM_ZLIB
    unset CFLAGS
    unset LDFLAGS
  fi
  pip install -U -q pip setuptools wheel
  # ref: https://github.com/grpc/grpc/issues/28387
  pip wheel -w ./wheelhouse --no-binary :all: grpcio grpcio-tools
  pyenv shell --unset
  pyenv uninstall -f tmp-grpcio-build
  echo "List of prebuilt wheels:"
  ls -l ./wheelhouse
  # Currently there are not many packages that provides prebuilt binaries for M1 Macs.
  # Let's configure necessary env-vars to build them locally via bdist_wheel.
  echo "Configuring additional build flags for local wheel builds for macOS on Apple Silicon ..."
  set_brew_python_build_flags
fi

# Install postgresql, etcd packages via docker
show_info "Launching the docker compose \"halfstack\"..."
mkdir -p "$HALFSTACK_VOLUME_PATH"
SOURCE_COMPOSE_PATH="docker-compose.halfstack-${CURRENT_BRANCH//.}.yml"
if [ ! -f "${SOURCE_COMPOSE_PATH}" ]; then
  SOURCE_COMPOSE_PATH="docker-compose.halfstack-main.yml"
fi
cp "${SOURCE_COMPOSE_PATH}" "docker-compose.halfstack.current.yml"
sed_inplace "s/8100:5432/${POSTGRES_PORT}:5432/" "docker-compose.halfstack.current.yml"
sed_inplace "s/8110:6379/${REDIS_PORT}:6379/" "docker-compose.halfstack.current.yml"
sed_inplace "s/8120:2379/${ETCD_PORT}:2379/" "docker-compose.halfstack.current.yml"
mkdir -p "${HALFSTACK_VOLUME_PATH}/postgres-data"
mkdir -p "${HALFSTACK_VOLUME_PATH}/etcd-data"
$docker_sudo docker compose -f "docker-compose.halfstack.current.yml" up -d
$docker_sudo docker compose -f "docker-compose.halfstack.current.yml" ps   # You should see three containers here.

check_snappy() {
  pip download python-snappy
  local pkgfile=$(ls | grep snappy)
  if [[ $pkgfile =~ .*\.tar.gz ]]; then
    # source build is required!
    install_system_pkg "libsnappy-dev" "snappy-devel" "snappy"
  fi
  rm -f $pkgfile
}

show_info "Creating the unified virtualenv for IDEs..."
check_snappy
$PANTS export '::'

if [ $ENABLE_CUDA -eq 1 ]; then
  if [ "$CUDA_BRANCH" == "mock" ]; then
    PLUGIN_BRANCH=$CUDA_BRANCH scripts/install-plugin.sh "lablup/backend.ai-accelerator-cuda-mock"
    cp "${PLUGIN_PATH}/backend.ai-accelerator-cuda-mock/configs/sample-mig.toml" cuda-mock.toml
  else
    PLUGIN_BRANCH=$CUDA_BRANCH scripts/install-plugin.sh "lablup/backend.ai-accelerator-cuda"
  fi
fi

# Copy default configurations
show_info "Copy default configuration files to manager / agent root..."
cp configs/manager/halfstack.toml ./manager.toml
sed_inplace "s/num-proc = .*/num-proc = 1/" ./manager.toml
sed_inplace "s/port = 8120/port = ${ETCD_PORT}/" ./manager.toml
sed_inplace "s/port = 8100/port = ${POSTGRES_PORT}/" ./manager.toml
sed_inplace "s/port = 8081/port = ${MANAGER_PORT}/" ./manager.toml
cp configs/manager/halfstack.alembic.ini ./alembic.ini
sed_inplace "s/localhost:8100/localhost:${POSTGRES_PORT}/" ./alembic.ini
./backend.ai mgr etcd put config/redis/addr "127.0.0.1:${REDIS_PORT}"
cp configs/manager/sample.etcd.volumes.json ./dev.etcd.volumes.json
MANAGER_AUTH_KEY=$(python -c 'import secrets; print(secrets.token_hex(32), end="")')
sed_inplace "s/\"secret\": \"some-secret-shared-with-storage-proxy\"/\"secret\": \"${MANAGER_AUTH_KEY}\"/" ./dev.etcd.volumes.json
sed_inplace "s/\"default_host\": .*$/\"default_host\": \"${LOCAL_STORAGE_PROXY}:${LOCAL_STORAGE_VOLUME}\",/" ./dev.etcd.volumes.json

cp configs/agent/halfstack.toml ./agent.toml
sed_inplace "s/port = 8120/port = ${ETCD_PORT}/" ./agent.toml
sed_inplace "s/port = 6001/port = ${AGENT_RPC_PORT}/" ./agent.toml
sed_inplace "s/port = 6009/port = ${AGENT_WATCHER_PORT}/" ./agent.toml

cp configs/storage-proxy/sample.toml ./storage-proxy.toml
STORAGE_PROXY_RANDOM_KEY=$(python -c 'import secrets; print(secrets.token_hex(32), end="")')
sed_inplace "s/secret = \"some-secret-private-for-storage-proxy\"/secret = \"${STORAGE_PROXY_RANDOM_KEY}\"/" ./storage-proxy.toml
sed_inplace "s/secret = \"some-secret-shared-with-manager\"/secret = \"${MANAGER_AUTH_KEY}\"/" ./storage-proxy.toml
# comment out all sample volumes
sed_inplace "s/^\[volume\./# \[volume\./" ./storage-proxy.toml
sed_inplace "s/^backend =/# backend =/" ./storage-proxy.toml
sed_inplace "s/^path =/# path =/" ./storage-proxy.toml
sed_inplace "s/^purity/# purity/" ./storage-proxy.toml
sed_inplace "s/^netapp_/# netapp_/" ./storage-proxy.toml

# add LOCAL_STORAGE_VOLUME vfs volume
echo "\n[volume.${LOCAL_STORAGE_VOLUME}]\nbackend = \"vfs\"\npath = \"${ROOT_PATH}/${VFOLDER_REL_PATH}\"" >> ./storage-proxy.toml

cp configs/webserver/sample.conf ./webserver.conf
sed_inplace "s/^port = 8080$/port = ${WEBSERVER_PORT}/" ./webserver.conf
sed_inplace "s/https:\/\/api.backend.ai/http:\/\/127.0.0.1:${MANAGER_PORT}/" ./webserver.conf
sed_inplace "s/ssl-verify = true/ssl-verify = false/" ./webserver.conf
sed_inplace "s/redis.port = 6379/redis.port = ${REDIS_PORT}/" ./webserver.conf

echo "export BACKENDAI_TEST_CLIENT_ENV=${PWD}/env-local-admin-api.sh" > ./env-tester-admin.sh
echo "export BACKENDAI_TEST_CLIENT_ENV=${PWD}/env-local-user-api.sh" > ./env-tester-user.sh

# DB schema
show_info "Setting up databases..."
./backend.ai mgr schema oneshot
./backend.ai mgr fixture populate fixtures/manager/example-keypairs.json
./backend.ai mgr fixture populate fixtures/manager/example-resource-presets.json

# Docker registry setup
show_info "Configuring the Lablup's official image registry..."
./backend.ai mgr etcd put config/docker/registry/cr.backend.ai "https://cr.backend.ai"
./backend.ai mgr etcd put config/docker/registry/cr.backend.ai/type "harbor2"
if [ "$(uname -m)" = "arm64" ] || [ "$(uname -m)" = "aarch64" ]; then
  ./backend.ai mgr etcd put config/docker/registry/cr.backend.ai/project "stable,community,multiarch"
else
  ./backend.ai mgr etcd put config/docker/registry/cr.backend.ai/project "stable,community"
fi

# Scan the container image registry
show_info "Scanning the image registry..."
./backend.ai mgr etcd rescan-images cr.backend.ai
if [ "$(uname -m)" = "arm64" ] || [ "$(uname -m)" = "aarch64" ]; then
  ./backend.ai mgr etcd alias python "cr.backend.ai/multiarch/python:3.9-ubuntu20.04" aarch64
else
  ./backend.ai mgr etcd alias python "cr.backend.ai/stable/python:3.9-ubuntu20.04" x86_64
fi

# Virtual folder setup
show_info "Setting up virtual folder..."
mkdir -p "${ROOT_PATH}/${VFOLDER_REL_PATH}"
./backend.ai mgr etcd put-json volumes "./dev.etcd.volumes.json"
mkdir -p scratches
POSTGRES_CONTAINER_ID=$($docker_sudo docker compose -f "docker-compose.halfstack.current.yml" ps | grep "[-_]backendai-half-db[-_]1" | awk '{print $1}')
$docker_sudo docker exec -it $POSTGRES_CONTAINER_ID psql postgres://postgres:develove@localhost:5432/backend database -c "update domains set allowed_vfolder_hosts = '{${LOCAL_STORAGE_PROXY}:${LOCAL_STORAGE_VOLUME}}';"
$docker_sudo docker exec -it $POSTGRES_CONTAINER_ID psql postgres://postgres:develove@localhost:5432/backend database -c "update groups set allowed_vfolder_hosts = '{${LOCAL_STORAGE_PROXY}:${LOCAL_STORAGE_VOLUME}}';"
$docker_sudo docker exec -it $POSTGRES_CONTAINER_ID psql postgres://postgres:develove@localhost:5432/backend database -c "update keypair_resource_policies set allowed_vfolder_hosts = '{${LOCAL_STORAGE_PROXY}:${LOCAL_STORAGE_VOLUME}}';"
$docker_sudo docker exec -it $POSTGRES_CONTAINER_ID psql postgres://postgres:develove@localhost:5432/backend database -c "update vfolders set host = '${LOCAL_STORAGE_PROXY}:${LOCAL_STORAGE_VOLUME}' where host='${LOCAL_STORAGE_VOLUME}';"

# Client backend endpoint configuration shell script
CLIENT_ADMIN_CONF_FOR_API="env-local-admin-api.sh"
CLIENT_ADMIN_CONF_FOR_SESSION="env-local-admin-session.sh"
echo "# Directly access to the manager using API keypair (admin)" >> "${CLIENT_ADMIN_CONF_FOR_API}"
echo "export BACKEND_ENDPOINT=http://127.0.0.1:${MANAGER_PORT}/" >> "${CLIENT_ADMIN_CONF_FOR_API}"
echo "export BACKEND_ACCESS_KEY=$(cat fixtures/manager/example-keypairs.json | jq -r '.keypairs[] | select(.user_id=="admin@lablup.com") | .access_key')" >> "${CLIENT_ADMIN_CONF_FOR_API}"
echo "export BACKEND_SECRET_KEY=$(cat fixtures/manager/example-keypairs.json | jq -r '.keypairs[] | select(.user_id=="admin@lablup.com") | .secret_key')" >> "${CLIENT_ADMIN_CONF_FOR_API}"
echo "export BACKEND_ENDPOINT_TYPE=api" >> "${CLIENT_ADMIN_CONF_FOR_API}"
chmod +x "${CLIENT_ADMIN_CONF_FOR_API}"
echo "# Indirectly access to the manager via the web server a using cookie-based login session (admin)" >> "${CLIENT_ADMIN_CONF_FOR_SESSION}"
echo "export BACKEND_ENDPOINT=http://127.0.0.1:${WEBSERVER_PORT}" >> "${CLIENT_ADMIN_CONF_FOR_SESSION}"
echo "unset BACKEND_ACCESS_KEY" >> "${CLIENT_ADMIN_CONF_FOR_SESSION}"
echo "unset BACKEND_SECRET_KEY" >> "${CLIENT_ADMIN_CONF_FOR_SESSION}"
echo "export BACKEND_ENDPOINT_TYPE=session" >> "${CLIENT_ADMIN_CONF_FOR_SESSION}"
echo "echo 'Run backend.ai login to make an active session.'" >> "${CLIENT_ADMIN_CONF_FOR_SESSION}"
echo "echo 'Username: $(cat fixtures/manager/example-keypairs.json | jq -r '.users[] | select(.username=="admin") | .email')'" >> "${CLIENT_ADMIN_CONF_FOR_SESSION}"
echo "echo 'Password: $(cat fixtures/manager/example-keypairs.json | jq -r '.users[] | select(.username=="admin") | .password')'" >> "${CLIENT_ADMIN_CONF_FOR_SESSION}"
chmod +x "${CLIENT_ADMIN_CONF_FOR_SESSION}"
CLIENT_DOMAINADMIN_CONF_FOR_API="env-local-domainadmin-api.sh"
CLIENT_DOMAINADMIN_CONF_FOR_SESSION="env-local-domainadmin-session.sh"
echo "# Directly access to the manager using API keypair (admin)" >> "${CLIENT_DOMAINADMIN_CONF_FOR_API}"
echo "export BACKEND_ENDPOINT=http://127.0.0.1:${MANAGER_PORT}/" >> "${CLIENT_DOMAINADMIN_CONF_FOR_API}"
echo "export BACKEND_ACCESS_KEY=$(cat fixtures/manager/example-keypairs.json | jq -r '.keypairs[] | select(.user_id=="domain-admin@lablup.com") | .access_key')" >> "${CLIENT_DOMAINADMIN_CONF_FOR_API}"
echo "export BACKEND_SECRET_KEY=$(cat fixtures/manager/example-keypairs.json | jq -r '.keypairs[] | select(.user_id=="domain-admin@lablup.com") | .secret_key')" >> "${CLIENT_DOMAINADMIN_CONF_FOR_API}"
echo "export BACKEND_ENDPOINT_TYPE=api" >> "${CLIENT_DOMAINADMIN_CONF_FOR_API}"
chmod +x "${CLIENT_DOMAINADMIN_CONF_FOR_API}"
echo "# Indirectly access to the manager via the web server a using cookie-based login session (admin)" >> "${CLIENT_DOMAINADMIN_CONF_FOR_SESSION}"
echo "export BACKEND_ENDPOINT=http://127.0.0.1:${WEBSERVER_PORT}" >> "${CLIENT_DOMAINADMIN_CONF_FOR_SESSION}"
echo "unset BACKEND_ACCESS_KEY" >> "${CLIENT_DOMAINADMIN_CONF_FOR_SESSION}"
echo "unset BACKEND_SECRET_KEY" >> "${CLIENT_DOMAINADMIN_CONF_FOR_SESSION}"
echo "export BACKEND_ENDPOINT_TYPE=session" >> "${CLIENT_DOMAINADMIN_CONF_FOR_SESSION}"
echo "echo 'Run backend.ai login to make an active session.'" >> "${CLIENT_DOMAINADMIN_CONF_FOR_SESSION}"
echo "echo 'Username: $(cat fixtures/manager/example-keypairs.json | jq -r '.users[] | select(.username=="domain-admin") | .email')'" >> "${CLIENT_DOMAINADMIN_CONF_FOR_SESSION}"
echo "echo 'Password: $(cat fixtures/manager/example-keypairs.json | jq -r '.users[] | select(.username=="domain-admin") | .password')'" >> "${CLIENT_DOMAINADMIN_CONF_FOR_SESSION}"
chmod +x "${CLIENT_DOMAINADMIN_CONF_FOR_SESSION}"
CLIENT_USER_CONF_FOR_API="env-local-user-api.sh"
CLIENT_USER_CONF_FOR_SESSION="env-local-user-session.sh"
echo "# Directly access to the manager using API keypair (user)" >> "${CLIENT_USER_CONF_FOR_API}"
echo "export BACKEND_ENDPOINT=http://127.0.0.1:${MANAGER_PORT}/" >> "${CLIENT_USER_CONF_FOR_API}"
echo "export BACKEND_ACCESS_KEY=$(cat fixtures/manager/example-keypairs.json | jq -r '.keypairs[] | select(.user_id=="user@lablup.com") | .access_key')" >> "${CLIENT_USER_CONF_FOR_API}"
echo "export BACKEND_SECRET_KEY=$(cat fixtures/manager/example-keypairs.json | jq -r '.keypairs[] | select(.user_id=="user@lablup.com") | .secret_key')" >> "${CLIENT_USER_CONF_FOR_API}"
echo "export BACKEND_ENDPOINT_TYPE=api" >> "${CLIENT_USER_CONF_FOR_API}"
chmod +x "${CLIENT_USER_CONF_FOR_API}"
echo "# Indirectly access to the manager via the web server a using cookie-based login session (user)" >> "${CLIENT_USER_CONF_FOR_SESSION}"
echo "export BACKEND_ENDPOINT=http://127.0.0.1:${WEBSERVER_PORT}" >> "${CLIENT_USER_CONF_FOR_SESSION}"
echo "unset BACKEND_ACCESS_KEY" >> "${CLIENT_USER_CONF_FOR_SESSION}"
echo "unset BACKEND_SECRET_KEY" >> "${CLIENT_USER_CONF_FOR_SESSION}"
echo "export BACKEND_ENDPOINT_TYPE=session" >> "${CLIENT_USER_CONF_FOR_SESSION}"
echo "echo 'Run backend.ai login to make an active session.'" >> "${CLIENT_USER_CONF_FOR_SESSION}"
echo "echo 'Username: $(cat fixtures/manager/example-keypairs.json | jq -r '.users[] | select(.username=="user") | .email')'" >> "${CLIENT_USER_CONF_FOR_SESSION}"
echo "echo 'Password: $(cat fixtures/manager/example-keypairs.json | jq -r '.users[] | select(.username=="user") | .password')'" >> "${CLIENT_USER_CONF_FOR_SESSION}"
chmod +x "${CLIENT_USER_CONF_FOR_SESSION}"

# TODO: Update tester env script
## sed_inplace "s@export BACKENDAI_TEST_CLIENT_VENV=/home/user/.pyenv/versions/venv-dev-client@export BACKENDAI_TEST_CLIENT_VENV=${VENV_PATH}@" ./env-tester-admin.sh
## sed_inplace "s@export BACKENDAI_TEST_CLIENT_ENV=/home/user/bai-dev/client-py/my-backend-session.sh@export BACKENDAI_TEST_CLIENT_ENV=${INSTALL_PATH}/client-py/${CLIENT_ADMIN_CONF_FOR_API}@" ./env-tester-admin.sh
## sed_inplace "s@export BACKENDAI_TEST_CLIENT_VENV=/home/user/.pyenv/versions/venv-dev-client@export BACKENDAI_TEST_CLIENT_VENV=${VENV_PATH}@" ./env-tester-user.sh
## sed_inplace "s@export BACKENDAI_TEST_CLIENT_ENV=/home/user/bai-dev/client-py/my-backend-session.sh@export BACKENDAI_TEST_CLIENT_ENV=${INSTALL_PATH}/client-py/${CLIENT_USER_CONF_FOR_API}@" ./env-tester-user.sh

show_info "Pre-pulling frequently used kernel images..."
echo "NOTE: Other images will be downloaded from the docker registry when requested.\n"
if [ "$(uname -m)" = "arm64" ] || [ "$(uname -m)" = "aarch64" ]; then
  $docker_sudo docker pull "cr.backend.ai/multiarch/python:3.9-ubuntu20.04"
else
  $docker_sudo docker pull "cr.backend.ai/stable/python:3.9-ubuntu20.04"
  if [ $DOWNLOAD_BIG_IMAGES -eq 1 ]; then
    $docker_sudo docker pull "cr.backend.ai/stable/python-tensorflow:2.7-py38-cuda11.3"
    $docker_sudo docker pull "cr.backend.ai/stable/python-pytorch:1.8-py38-cuda11.1"
  fi
fi

show_info "Installation finished."
show_note "Check out the default API keypairs and account credentials for local development and testing:"
echo "> ${WHITE}cat env-local-admin-api.sh${NC}"
echo "> ${WHITE}cat env-local-admin-session.sh${NC}"
echo "> ${WHITE}cat env-local-domainadmin-api.sh${NC}"
echo "> ${WHITE}cat env-local-domainadmin-session.sh${NC}"
echo "> ${WHITE}cat env-local-user-api.sh${NC}"
echo "> ${WHITE}cat env-local-user-session.sh${NC}"
show_note "To apply the client config, source one of the configs like:"
echo "> ${WHITE}source env-local-user-session.sh${NC}"
echo " "
show_note "Your pants invocation command:"
echo "> ${WHITE}${PANTS}${NC}"
echo " "
show_important_note "You should change your default admin API keypairs for production environment!"
show_note "How to run Backend.AI manager:"
echo "> ${WHITE}./backend.ai mgr start-server --debug${NC}"
show_note "How to run Backend.AI agent:"
echo "> ${WHITE}./backend.ai ag start-server --debug${NC}"
show_note "How to run Backend.AI storage-proxy:"
echo "> ${WHITE}./py -m ai.backend.storage.server${NC}"
show_note "How to run Backend.AI web server (for ID/Password login):"
echo "> ${WHITE}./py -m ai.backend.web.server${NC}"
show_note "How to run your first code:"
echo "> ${WHITE}./backend.ai --help${NC}"
echo "> ${WHITE}source env-local-admin-api.sh${NC}"
echo "> ${WHITE}./backend.ai run python -c \"print('Hello World\\!')\"${NC}"
echo " "
echo "${GREEN}Development environment is now ready.${NC}"
show_note "How to run docker-compose:"
if [ ! -z "$docker_sudo" ]; then
  echo "    > ${WHITE}${docker_sudo} docker compose -f docker-compose.halfstack.current.yml up -d ...${NC}"
else
  echo "    > ${WHITE}docker compose -f docker-compose.halfstack.current.yml up -d ...${NC}"
fi
show_note "How to reset this setup:"
echo "    > ${WHITE}$(dirname $0)/delete-dev.sh${NC}"
echo " "

# vim: tw=0 sts=2 sw=2 et
