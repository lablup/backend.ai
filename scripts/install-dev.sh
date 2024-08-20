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
BOLD="\033[1m"
UNDL="\033[4m"
RVRS="\033[7m"
NC="\033[0m"
REWRITELN="\033[A\r\033[K"

readlinkf() {
  $bpython -c "import os,sys; print(os.path.realpath(os.path.expanduser(sys.argv[1])))" "${1}"
}

relpath() {
  $bpython -c "import os.path; print(os.path.relpath('$1','${2:-$PWD}'))"
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
  echo "  ${LWHITE}--show-guide${NC}"
  echo "    Show the guide generated after the installation"
  echo ""
  echo "  ${LWHITE}--enable-cuda${NC}"
  echo "    Install CUDA accelerator plugin and pull a"
  echo "    TensorFlow CUDA kernel for testing/demo."
  echo "    (default: false)"
  echo ""
  echo "  ${LWHITE}--enable-cuda-mock${NC}"
  echo "    Install CUDA accelerator mock plugin and pull a"
  echo "    TensorFlow CUDA kernel for testing/demo."
  echo "    (default: false)"
  echo ""
  echo "  ${LWHITE}--editable-webui${NC}"
  echo "    Install the webui as an editable repository under src/ai/backend/webui."
  echo "    If you are on the main branch, this will be automatically enabled."
  echo ""
  echo "  ${LWHITE}--postgres-port PORT${NC}"
  echo "    The port to bind the PostgreSQL container service."
  echo "    (default: 8101)"
  echo ""
  echo "  ${LWHITE}--redis-port PORT${NC}"
  echo "    The port to bind the Redis container service."
  echo "    (default: 8111)"
  echo ""
  echo "  ${LWHITE}--etcd-port PORT${NC}"
  echo "    The port to bind the etcd container service."
  echo "    (default: 8121)"
  echo ""
  echo "  ${LWHITE}--webserver-port PORT${NC}"
  echo "    The port to expose the web server."
  echo "    (default: 8090)"
  echo ""
  echo "  ${LWHITE}--manager-port PORT${NC}"
  echo "    The port to expose the manager API service."
  echo "    (default: 8091)"
  echo ""
  echo "  ${LWHITE}--agent-rpc-port PORT${NC}"
  echo "    The port for the manager-to-agent RPC calls."
  echo "    (default: 6011)"
  echo ""
  echo "  ${LWHITE}--agent-watcher-port PORT${NC}"
  echo "    The port for the agent's watcher service."
  echo "    (default: 6019)"
  echo ""
  echo "  ${LWHITE}--agent-backend mode${NC}"
  echo "    Mode for backend agent(docker, kubernetes)."
  echo "    (default: docker)"
  echo ""
  echo "  ${LWHITE}--ipc-base-path PATH${NC}"
  echo "    The base path for IPC sockets and shared temporary files."
  echo "    (default: /tmp/backend.ai/ipc)"
  echo ""
  echo "  ${LWHITE}--var-base-path PATH${NC}"
  echo "    The base path for shared data files."
  echo "    (default: ./var/lib/backend.ai)"
  echo ""
  echo "  ${LWHITE}--configure-ha${NC}"
  echo "    Configure HA dev environment."
  echo "    (default: false)"
}

show_error() {
  echo " "
  echo "${RED}[ERROR]${NC} ${LRED}$1${NC}"
}

show_warning() {
  echo " "
  echo "${LRED}[WARN]${NC} ${LYELLOW}$1${NC}"
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
  echo "${LRED}[NOTE]${NC} ${LYELLOW}$1${NC}"
}

show_guide() {
  show_note "Check out the default API keypairs and account credentials for local development and testing:"
  echo "  > ${WHITE}cat env-local-admin-api.sh${NC}"
  echo "  > ${WHITE}cat env-local-admin-session.sh${NC}"
  echo "  > ${WHITE}cat env-local-domainadmin-api.sh${NC}"
  echo "  > ${WHITE}cat env-local-domainadmin-session.sh${NC}"
  echo "  > ${WHITE}cat env-local-user-api.sh${NC}"
  echo "  > ${WHITE}cat env-local-user-session.sh${NC}"
  show_note "To apply the client config, source one of the configs like:"
  echo "  > ${WHITE}source env-local-user-session.sh${NC}"
  show_important_note "You should change your default admin API keypairs in any public/production setups!"
  show_note "How to run Backend.AI manager:"
  echo "  > ${WHITE}./backend.ai mgr start-server --debug${NC}"
  show_note "How to run Backend.AI agent:"
  echo "  > ${WHITE}./backend.ai ag start-server --debug${NC}"
  show_note "How to run Backend.AI storage-proxy:"
  echo "  > ${WHITE}./py -m ai.backend.storage.server${NC}"
  show_note "How to run Backend.AI web server (for ID/Password login and Web UI):"
  echo "  > ${WHITE}./py -m ai.backend.web.server${NC}"
  show_note "How to run Backend.AI wsproxy:"
  echo "  > ${WHITE}./py -m ai.backend.wsproxy.server${NC}"
  echo "  ${LRED}DO NOT source env-local-*.sh in the shell where you run the web server"
  echo "  to prevent misbehavior of the client used inside the web server.${NC}"
  show_info "How to run your first code:"
  echo "  > ${WHITE}./backend.ai --help${NC}"
  echo "  > ${WHITE}source env-local-admin-api.sh${NC}"
  echo "  > ${WHITE}./backend.ai run python -c \"print('Hello World\\!')\"${NC}"
  show_info "How to run docker-compose:"
  if [ ! -z "$docker_sudo" ]; then
    echo "  > ${WHITE}${docker_sudo} docker compose -f docker-compose.halfstack.current.yml up -d ...${NC}"
  else
    echo "  > ${WHITE}docker compose -f docker-compose.halfstack.current.yml up -d ...${NC}"
  fi
  if [ $EDITABLE_WEBUI -eq 1 ]; then
    show_info "How to run the editable checkout of webui:"
    echo "(Terminal 1)"
    echo "  > ${WHITE}cd src/ai/backend/webui; npm run build:d${NC}"
    echo "(Terminal 2)"
    echo "  > ${WHITE}cd src/ai/backend/webui; npm run server:d${NC}"
    echo "If you just run ${WHITE}./py -m ai.backend.web.server${NC}, it will use the local version compiled from the checked out source."
  fi
  show_info "Manual configuration for the client accessible hostname in various proxies"
  echo " "
  echo "If you use a VM for this development setup but access it from a web browser outside the VM or remote nodes,"
  echo "you must manually modify the following configurations to use an IP address or a DNS hostname"
  echo "that can be accessible from both the client SDK and the web browser."
  echo " "
  echo " - ${YELLOW}volumes/proxies/local/client_api${CYAN} etcd key${NC}"
  echo " - ${YELLOW}apiEndpoint${NC}, ${YELLOW}proxyURL${NC}, ${YELLOW}webServerURL${NC} of ${CYAN}src/ai/backend/webui/config.toml${NC}"
  echo " - ${YELLOW}PROXYBASEHOST${NC} of ${CYAN}src/ai/backend/webui/.env${NC}"
  echo " "
  echo "We recommend setting ${BOLD}/etc/hosts${NC}${WHITE} in both the VM and your web browser's host${NC} to keep a consistent DNS hostname"
  echo "of the storage-proxy's client API endpoint."
  echo " "
  echo "An example command to change the value of that key:"
  echo "  > ${WHITE}./backend.ai mgr etcd put volumes/proxies/local/client_api http://my-dev-machine:6021${NC}"
  echo "where /etc/hosts in the VM contains:"
  echo "  ${WHITE}127.0.0.1      my-dev-machine${NC}"
  echo "and where /etc/hosts in the web browser host contains:"
  echo "  ${WHITE}192.168.99.99  my-dev-machine${NC}"
  show_info "How to reset this setup:"
  echo "  > ${WHITE}$(dirname $0)/delete-dev.sh${NC}"
  echo "  ${LRED}This will delete all your database!${NC}"
  echo " "
  if [ $_INSTALLED_PYENV -eq 1 ]; then
    show_info "About pyenv installation:"
    echo "Since we have installed ${BOLD}pyenv${NC} during setup, you should reload the shell to make it working as expected."
    echo "Run the following command or re-login:"
    echo "  ${WHITE}exec \$SHELL -l${NC}"
  fi
}

if [[ "$OSTYPE" == "linux-gnu" ]]; then
  if [ $(id -u) = "0" ]; then
    docker_sudo=''
  else
    docker_sudo='sudo -E'
  fi
else
  docker_sudo=''
fi
if [ $(id -u) = "0" ]; then
  sudo=''
else
  sudo='sudo -E'
fi

# Detect distribution
KNOWN_DISTRO="(Debian|Ubuntu|RedHat|CentOS|openSUSE|Amazon|Arista|SUSE)"
DISTRO=$(lsb_release -d 2>/dev/null | grep -Eo $KNOWN_DISTRO  || grep -Eo $KNOWN_DISTRO /etc/issue 2>/dev/null || uname -s)

if [ $DISTRO = "Darwin" ]; then
  DISTRO="Darwin"
  STANDALONE_PYTHON_PLATFORM="apple-darwin"
elif [ -f /etc/debian_version -o "$DISTRO" == "Debian" -o "$DISTRO" == "Ubuntu" ]; then
  DISTRO="Debian"
  STANDALONE_PYTHON_PLATFORM="unknown-linux-gnu"
elif [ -f /etc/redhat-release -o "$DISTRO" == "RedHat" -o "$DISTRO" == "CentOS" -o "$DISTRO" == "Amazon" ]; then
  DISTRO="RedHat"
  STANDALONE_PYTHON_PLATFORM="unknown-linux-gnu"
elif [ -f /etc/system-release -o "$DISTRO" == "Amazon" ]; then
  DISTRO="RedHat"
  STANDALONE_PYTHON_PLATFORM="unknown-linux-gnu"
elif [ -f /usr/lib/os-release -o "$DISTRO" == "SUSE" ]; then
  DISTRO="SUSE"
  STANDALONE_PYTHON_PLATFORM="unknown-linux-gnu"
else
  show_error "Sorry, your host OS distribution is not supported by this script."
  show_info "Please send us a pull request or file an issue to support your environment!"
  exit 1
fi

show_info "Checking the bootstrapper Python version..."
source scripts/bootstrap-static-python.sh
$bpython -c 'import sys;print(sys.version_info)'

ROOT_PATH="$(pwd)"
if [ ! -f "${ROOT_PATH}/BUILD_ROOT" ]; then
  show_error "BUILD_ROOT is not found!"
  echo "You are not on the root directory of the repository checkout."
  echo "Please \`cd\` there and run \`./scripts/install-dev.sh <args>\`"
  exit 1
fi
PLUGIN_PATH=$(relpath "${ROOT_PATH}/plugins")
HALFSTACK_VOLUME_PATH=$(relpath "${ROOT_PATH}/volumes")
PANTS_VERSION=$($bpython scripts/tomltool.py -f pants.toml get 'GLOBAL.pants_version')
PYTHON_VERSION=$($bpython scripts/tomltool.py -f pants.toml get 'python.interpreter_constraints[0]' | awk -F '==' '{print $2}')
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)

SHOW_GUIDE=0
ENABLE_CUDA=0
ENABLE_CUDA_MOCK=0
CONFIGURE_HA=0
EDITABLE_WEBUI=0
POSTGRES_PORT="8101"
[[ "$@" =~ "configure-ha" ]] && REDIS_PORT="8210" || REDIS_PORT="8111"
[[ "$@" =~ "configure-ha" ]] && ETCD_PORT="8220" || ETCD_PORT="8121"

MANAGER_PORT="8091"
WEBSERVER_PORT="8090"
WSPROXY_PORT="5050"
AGENT_RPC_PORT="6011"
AGENT_WATCHER_PORT="6019"
AGENT_BACKEND="docker"
IPC_BASE_PATH="/tmp/backend.ai/ipc"
VAR_BASE_PATH=$(relpath "${ROOT_PATH}/var/lib/backend.ai")
VFOLDER_REL_PATH="vfroot/local"
LOCAL_STORAGE_PROXY="local"
# MUST be one of the real storage volumes
LOCAL_STORAGE_VOLUME="volume1"
CODESPACES_ON_CREATE=0
CODESPACES_POST_CREATE=0
CODESPACES=${CODESPACES:-"false"}
_INSTALLED_PYENV=0

# Only Used in HA mode
REDIS_MASTER_PORT="9500"
REDIS_SLAVE1_PORT="9501"
REDIS_SLAVE2_PORT="9502"
REDIS_SENTINEL1_PORT="9503"
REDIS_SENTINEL2_PORT="9504"
REDIS_SENTINEL3_PORT="9505"

while [ $# -gt 0 ]; do
  case $1 in
    -h | --help)           usage; exit 1 ;;
    --show-guide)          SHOW_GUIDE=1 ;;
    --python-version)      PYTHON_VERSION=$2; shift ;;
    --python-version=*)    PYTHON_VERSION="${1#*=}" ;;
    --enable-cuda)         ENABLE_CUDA=1 ;;
    --enable-cuda-mock)    ENABLE_CUDA_MOCK=1 ;;
    --editable-webui)      EDITABLE_WEBUI=1 ;;
    --postgres-port)       POSTGRES_PORT=$2; shift ;;
    --postgres-port=*)     POSTGRES_PORT="${1#*=}" ;;
    --redis-port)          REDIS_PORT=$2; shift ;;
    --redis-port=*)        REDIS_PORT="${1#*=}" ;;
    --etcd-port)           ETCD_PORT=$2; shift ;;
    --etcd-port=*)         ETCD_PORT="${1#*=}" ;;
    --manager-port)         MANAGER_PORT=$2; shift ;;
    --manager-port=*)       MANAGER_PORT="${1#*=}" ;;
    --webserver-port)       WEBSERVER_PORT=$2; shift ;;
    --webserver-port=*)     WEBSERVER_PORT="${1#*=}" ;;
    --agent-rpc-port)       AGENT_RPC_PORT=$2; shift ;;
    --agent-rpc-port=*)     AGENT_RPC_PORT="${1#*=}" ;;
    --agent-watcher-port)   AGENT_WATCHER_PORT=$2; shift ;;
    --agent-watcher-port=*) AGENT_WATCHER_PORT="${1#*=}" ;;
    --ipc-base-path)        IPC_BASE_PATH=$2; shift ;;
    --ipc-base-path=*)      IPC_BASE_PATH="${1#*=}" ;;
    --var-base-path)        VAR_BASE_PATH=$2; shift ;;
    --var-base-path=*)      VAR_BASE_PATH="${1#*=}" ;;
    --codespaces-on-create) CODESPACES_ON_CREATE=1 ;;
    --codespaces-post-create) CODESPACES_POST_CREATE=1 ;;
    --agent-backend)        AGENT_BACKEND=$2; shift ;;
    --agent-backend=*)      AGENT_BACKEND="${1#*=}" ;;
    --configure-ha)         CONFIGURE_HA=1 ;;
    *)
      echo "Unknown option: $1"
      echo "Run '$0 --help' for usage."
      exit 1
  esac
  shift
done
if [ "$CURRENT_BRANCH" = "main" ]; then
  EDITABLE_WEBUI=1  # auto-enable if we're on the main branch
fi

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
  SUSE)
    $sudo zypper update
    $sudo zypper install -y git jq gcc make gcc-c++
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
  SUSE)
    $sudo zypper update
    $sudo zypper install -y openssl-devel readline-devel gdbm-devel zlib-devel libbz2-devel sqlite3-devel libffi-devel xz-devel
    ;;
  Darwin)
    brew install openssl
    brew install readline
    brew install zlib xz
    brew install sqlite3 gdbm
    brew install tcl-tk
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
  SUSE)
    $sudo zypper install -y git-lfs
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
  SUSE)
    $sudo zypper install -y $2
    ;;
  Darwin)
    brew install $3
  esac
}

install_node() {
  if ! command -v nvm &> /dev/null; then
    show_info "Installing latest version of NVM..."
    curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.5/install.sh | bash
    export NVM_DIR="$([ -z "${XDG_CONFIG_HOME-}" ] && printf %s "${HOME}/.nvm" || printf %s "${XDG_CONFIG_HOME}/nvm")"
    [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh" # This loads nvm
  fi

  node_version=$(curl -sL https://raw.githubusercontent.com/lablup/backend.ai-webui/main/.nvmrc)
  show_info "Installing Node.js v${node_version} via NVM..."
  nvm install $node_version
  nvm use node
}

set_brew_python_build_flags() {
  local _prefix_openssl="$(brew --prefix openssl)"
  local _prefix_sqlite3="$(brew --prefix sqlite3)"
  local _prefix_readline="$(brew --prefix readline)"
  local _prefix_zlib="$(brew --prefix zlib)"
  local _prefix_gdbm="$(brew --prefix gdbm)"
  local _prefix_tcltk="$(brew --prefix tcl-tk)"
  local _prefix_xz="$(brew --prefix xz)"
  local _prefix_libffi="$(brew --prefix libffi)"
  local _prefix_protobuf="$(brew --prefix protobuf)"
  export CFLAGS="-I${_prefix_openssl}/include -I${_prefix_sqlite3}/include -I${_prefix_readline}/include -I${_prefix_zlib}/include -I${_prefix_gdbm}/include -I${_prefix_tcltk}/include -I${_prefix_xz}/include -I${_prefix_libffi}/include -I${_prefix_protobuf}/include"
  export LDFLAGS="-L${_prefix_openssl}/lib -L${_prefix_sqlite3}/lib -L${_prefix_readline}/lib -L${_prefix_zlib}/lib -L${_prefix_gdbm}/lib -L${_prefix_tcltk}/lib -L${_prefix_xz}/lib -L${_prefix_libffi}/lib -L${_prefix_protobuf}/lib"
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
    echo "✓ Python ${PYTHON_VERSION} as the Backend.AI runtime is already installed."
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
      cat scripts/pre-commit >> .git/hooks/pre-commit
    fi
  else
    cp scripts/pre-commit .git/hooks/pre-commit
    chmod +x .git/hooks/pre-commit
  fi
  local magic_str="monorepo standard pre-push hook"
  if [ -f .git/hooks/pre-push ]; then
    grep -Fq "$magic_str" .git/hooks/pre-push
    if [ $? -eq 0 ]; then
      :
    else
      echo "" >> .git/hooks/pre-push
      cat scripts/pre-push >> .git/hooks/pre-push
    fi
  else
    cp scripts/pre-push .git/hooks/pre-push
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
  pants_local_exec_root=$($docker_sudo $bpython scripts/check-docker.py --get-preferred-pants-local-exec-root)
  mkdir -p "$pants_local_exec_root"
  $bpython scripts/tomltool.py -f .pants.rc set 'GLOBAL.local_execution_root_dir' "$pants_local_exec_root"
  set +e
  if command -v pants &> /dev/null ; then
    echo "Pants system command is already installed."
  else
    case $DISTRO in
    Darwin)
      brew install pantsbuild/tap/pants
      ;;
    *)
      curl --proto '=https' --tlsv1.2 -fsSL https://static.pantsbuild.org/setup/get-pants.sh > /tmp/get-pants.sh
      bash /tmp/get-pants.sh
      if ! command -v pants &> /dev/null ; then
        $sudo ln -s $HOME/.local/bin/pants /usr/local/bin/pants
        show_note "Symlinked $HOME/.local/bin/pants from /usr/local/bin/pants as we could not find it from PATH..."
      fi
      ;;
    esac
  fi
  pants version
  if [ $? -eq 1 ]; then
    # If we can't find the prebuilt Pants package, then try the source installation.
    show_error "Cannot proceed the installation because Pants is not available for your platform!"
    exit 1
  fi
  set -e
}

install_editable_webui() {
  if ! command -v node &> /dev/null; then
    install_node
  fi
  if ! command -v pnpm &> /dev/null; then
    show_info "Installing pnpm..."
    npm install -g pnpm
  fi
  show_info "Installing editable version of Web UI..."
  if [ -d "./src/ai/backend/webui" ]; then
    echo "src/ai/backend/webui already exists, so running 'make clean' on it..."
    cd src/ai/backend/webui
    make clean
  else
    git clone https://github.com/lablup/backend.ai-webui ./src/ai/backend/webui
    cd src/ai/backend/webui
    cp configs/default.toml config.toml
    local site_name=$(basename $(pwd))
    # The debug mode here is only for 'hard-core' debugging scenarios -- it changes lots of behaviors.
    # (e.g., separate debugging of Electron's renderer and main threads)
    sed_inplace "s@debug = true@debug = false@" config.toml
    # The webserver endpoint to use in the session mode.
    sed_inplace "s@#[[:space:]]*apiEndpoint =.*@apiEndpoint = "'"'"http://127.0.0.1:${WEBSERVER_PORT}"'"@' config.toml
    sed_inplace "s@#[[:space:]]*apiEndpointText =.*@apiEndpointText = "'"'"${site_name}"'"@' config.toml
    # webServerURL lets the electron app use the web UI contents from the server.
    # The server may be either a `npm run server:d` instance or a `./py -m ai.backend.web.server` instance.
    # In the former case, you may live-edit the webui sources while running them in the electron app.
    sed_inplace "s@webServerURL =.*@webServerURL = "'"'"http://127.0.0.1:${WEBSERVER_PORT}"'"@' config.toml
    sed_inplace "s@proxyURL =.*@proxyURL = "'"'"http://127.0.0.1:${WSPROXY_PORT}"'"@' config.toml
    echo "PROXYLISTENIP=0.0.0.0" >> .env
    echo "PROXYBASEHOST=localhost" >> .env
    echo "PROXYBASEPORT=${WSPROXY_PORT}" >> .env
  fi
  pnpm i
  make compile
  cd ../../../..
}

# BEGIN!

echo " "
echo "${LGREEN}Backend.AI one-line installer for developers${NC}"

if [ $SHOW_GUIDE -eq 1 ]; then
  show_guide
  exit 0
fi

# Check prerequisites
show_info "Checking prerequisites and script dependencies..."
install_script_deps
$bpython -m ensurepip --upgrade
# FIXME: Remove urllib3<2.0 requirement after docker/docker-py#3113 is resolved
$bpython -m pip --disable-pip-version-check install -q -U 'urllib3<2.0' aiohttp
if [ $CODESPACES != "true" ] || [ $CODESPACES_ON_CREATE -eq 1 ]; then
  $docker_sudo $bpython scripts/check-docker.py
  if [ $? -ne 0 ]; then
    exit 1
  fi
  # checking docker compose v2 -f flag
  if $(docker compose -f 2>&1 | grep -q 'unknown shorthand flag'); then
    show_error "When run as a user, 'docker compose' seems not to be a compatible version (v2)."
    show_info "Please check the following link: https://docs.docker.com/compose/install/ to install Docker Compose and its CLI plugin on ${HOME}/.docker/cli-plugins"
    exit 1
  fi
  if $(sudo docker compose -f 2>&1 | grep -q 'unknown shorthand flag'); then
    show_error "When run as the root, 'docker compose' seems not to be a compatible version (v2)"
    show_info "Please check the following link: https://docs.docker.com/compose/install/ to install Docker Compose and its CLI plugin on /usr/local/lib/docker/cli-plugins"
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
fi

if [ $ENABLE_CUDA -eq 1 ] && [ $ENABLE_CUDA_MOCK -eq 1 ]; then
  show_error "You can't use both CUDA and CUDA mock plugins at once!"
  show_error "Please remove --enable-cuda or --enable-cuda-mock flag to continue."
  exit 1
fi

read -r -d '' pyenv_init_script <<"EOS"
export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init --path)"
eval "$(pyenv init -)"
eval "$(pyenv virtualenv-init -)"
EOS

setup_environment() {
  # Install pyenv
  if ! type "pyenv" >/dev/null 2>&1; then
    if [ -d "$HOME/.pyenv" ]; then
      eval "$pyenv_init_script"
      pyenv --version
    fi
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
    pyenv --version
    _INSTALLED_PYENV=1
  else
    eval "$pyenv_init_script"
  fi

  # Install Python and pyenv virtualenvs
  show_info "Checking and installing Python dependencies..."
  install_pybuild_deps

  show_info "Setting additional git configs..."
  git config blame.ignoreRevsFile .git-blame-ignore-revs

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
  pyenv shell "${PYTHON_VERSION}"

  show_info "Bootstrapping the Pants build system..."
  bootstrap_pants

  set -e

  # Make directories
  show_info "Using the current working-copy directory as the installation path..."

  show_info "Creating the unified virtualenv for IDEs..."
  pants export \
    --resolve=python-default \
    --resolve=python-kernel \
    --resolve=pants-plugins \
    --resolve=towncrier \
    --resolve=ruff \
    --resolve=mypy \
    --resolve=black
  # NOTE: Some resolves like pytest are not needed to be exported at this point
  # because pants will generate temporary resolves when actually running the test cases.

  # Install postgresql, etcd packages via docker
  show_info "Creating docker compose configuration file for \"halfstack\"..."
  mkdir -p "$HALFSTACK_VOLUME_PATH"
  if [ $CONFIGURE_HA -eq 1 ]; then
    SOURCE_COMPOSE_PATH="docker-compose.halfstack-ha.yml"

    cp "${SOURCE_COMPOSE_PATH}" "docker-compose.halfstack.current.yml"
    sed_inplace "s/8100:5432/${POSTGRES_PORT}:5432/" "docker-compose.halfstack.current.yml"
    sed_inplace "s/8110:6379/${REDIS_PORT}:6379/" "docker-compose.halfstack.current.yml"
    sed_inplace "s/8120:2379/${ETCD_PORT}:2379/" "docker-compose.halfstack.current.yml"

    sed_inplace 's/\${REDIS_MASTER_PORT}/9500/g' "docker-compose.halfstack.current.yml"
    sed_inplace 's/\${REDIS_SLAVE1_PORT}/9501/g' "docker-compose.halfstack.current.yml"
    sed_inplace 's/\${REDIS_SLAVE2_PORT}/9502/g' "docker-compose.halfstack.current.yml"
    sed_inplace 's/\${REDIS_SENTINEL1_PORT}/9503/g' "docker-compose.halfstack.current.yml"
    sed_inplace 's/\${REDIS_SENTINEL2_PORT}/9504/g' "docker-compose.halfstack.current.yml"
    sed_inplace 's/\${REDIS_SENTINEL3_PORT}/9505/g' "docker-compose.halfstack.current.yml"

    mkdir -p "./tmp/backend.ai-halfstack-ha/configs"

    sentinel01_cfg_path="./tmp/backend.ai-halfstack-ha/configs/sentinel01.conf"
    sentinel02_cfg_path="./tmp/backend.ai-halfstack-ha/configs/sentinel02.conf"
    sentinel03_cfg_path="./tmp/backend.ai-halfstack-ha/configs/sentinel03.conf"

    cp ./configs/redis/sentinel.conf $sentinel01_cfg_path
    cp ./configs/redis/sentinel.conf $sentinel02_cfg_path
    cp ./configs/redis/sentinel.conf $sentinel03_cfg_path

    sed_inplace "s/\${COMPOSE_PATH}/${ROOT_PATH//\//\\/}\/tmp\/backend\.ai-halfstack-ha\/configs\//g" "docker-compose.halfstack.current.yml"

    # Appends the given text to sentinel01.conf
    echo "" >> $sentinel01_cfg_path
    sed_inplace "s/REDIS_SENTINEL_SELF_HOST/sentinel01/g" "$sentinel01_cfg_path"
    sed_inplace "s/REDIS_PASSWORD/develove/g" "$sentinel01_cfg_path"
    sed_inplace "s/REDIS_SENTINEL_SELF_PORT/9503/g" "$sentinel01_cfg_path"

    # Appends the given text to sentinel02.conf
    echo "" >> $sentinel02_cfg_path
    sed_inplace "s/REDIS_SENTINEL_SELF_HOST/sentinel02/g" "$sentinel02_cfg_path"
    sed_inplace "s/REDIS_PASSWORD/develove/g" "$sentinel02_cfg_path"
    sed_inplace "s/REDIS_SENTINEL_SELF_PORT/9504/g" "$sentinel02_cfg_path"

    # Appends the given text to sentinel03.conf
    echo "" >> $sentinel03_cfg_path
    sed_inplace "s/REDIS_SENTINEL_SELF_HOST/sentinel03/g" "$sentinel03_cfg_path"
    sed_inplace "s/REDIS_PASSWORD/develove/g" "$sentinel03_cfg_path"
    sed_inplace "s/REDIS_SENTINEL_SELF_PORT/9505/g" "$sentinel03_cfg_path"
  else
    SOURCE_COMPOSE_PATH="docker-compose.halfstack-${CURRENT_BRANCH//.}.yml"
    if [ ! -f "${SOURCE_COMPOSE_PATH}" ]; then
      SOURCE_COMPOSE_PATH="docker-compose.halfstack-main.yml"
    fi
    cp "${SOURCE_COMPOSE_PATH}" "docker-compose.halfstack.current.yml"
  fi

  sed_inplace "s/8100:5432/${POSTGRES_PORT}:5432/" "docker-compose.halfstack.current.yml"
  sed_inplace "s/8110:6379/${REDIS_PORT}:6379/" "docker-compose.halfstack.current.yml"
  sed_inplace "s/8120:2379/${ETCD_PORT}:2379/" "docker-compose.halfstack.current.yml"

  mkdir -p "${HALFSTACK_VOLUME_PATH}/postgres-data"
  mkdir -p "${HALFSTACK_VOLUME_PATH}/etcd-data"
  mkdir -p "${HALFSTACK_VOLUME_PATH}/redis-data"

  $docker_sudo docker compose -f "docker-compose.halfstack.current.yml" pull

  show_info "Pre-pulling frequently used kernel images..."
  echo "NOTE: Other images will be downloaded from the docker registry when requested.\n"
  if [ "$(uname -m)" = "arm64" ] || [ "$(uname -m)" = "aarch64" ]; then
    $docker_sudo docker pull "cr.backend.ai/multiarch/python:3.9-ubuntu20.04"
  else
    $docker_sudo docker pull "cr.backend.ai/stable/python:3.9-ubuntu20.04"
  fi
}

configure_backendai() {
  show_info "Creating docker compose \"halfstack\"..."
  $docker_sudo docker compose -f "docker-compose.halfstack.current.yml" up -d
  $docker_sudo docker compose -f "docker-compose.halfstack.current.yml" ps   # You should see three containers here.

  if [ $ENABLE_CUDA_MOCK -eq 1 ]; then
    cp "configs/accelerator/mock-accelerator.toml" mock-accelerator.toml
  fi

  # configure manager
  show_info "Copy default configuration files to manager / agent root..."
  cp configs/manager/halfstack.toml ./manager.toml
  sed_inplace "s/num-proc = .*/num-proc = 1/" ./manager.toml
  sed_inplace "s/port = 8120/port = ${ETCD_PORT}/" ./manager.toml
  sed_inplace "s/port = 8100/port = ${POSTGRES_PORT}/" ./manager.toml
  sed_inplace "s/port = 8081/port = ${MANAGER_PORT}/" ./manager.toml
  sed_inplace "s@\(# \)\{0,1\}ipc-base-path = .*@ipc-base-path = "'"'"${IPC_BASE_PATH}"'"'"@" ./manager.toml
  cp configs/manager/halfstack.alembic.ini ./alembic.ini
  sed_inplace "s/localhost:8100/localhost:${POSTGRES_PORT}/" ./alembic.ini

  if [ $CONFIGURE_HA -eq 1 ]; then
    ./backend.ai mgr etcd put config/redis/sentinel "127.0.0.1:${REDIS_SENTINEL1_PORT},127.0.0.1:${REDIS_SENTINEL2_PORT},127.0.0.1:${REDIS_SENTINEL3_PORT}"
    ./backend.ai mgr etcd put config/redis/service_name "mymaster"
    ./backend.ai mgr etcd put config/redis/password "develove"
  else
    ./backend.ai mgr etcd put config/redis/addr "127.0.0.1:${REDIS_PORT}"
  fi

  ./backend.ai mgr etcd put-json config/redis/redis_helper_config ./configs/manager/sample.etcd.redis-helper.json

  cp configs/manager/sample.etcd.volumes.json ./dev.etcd.volumes.json
  MANAGER_AUTH_KEY=$(python -c 'import secrets; print(secrets.token_hex(32), end="")')
  sed_inplace "s/\"secret\": \"some-secret-shared-with-storage-proxy\"/\"secret\": \"${MANAGER_AUTH_KEY}\"/" ./dev.etcd.volumes.json
  sed_inplace "s/\"default_host\": .*$/\"default_host\": \"${LOCAL_STORAGE_PROXY}:${LOCAL_STORAGE_VOLUME}\",/" ./dev.etcd.volumes.json

  # configure halfstack ports
  cp configs/agent/halfstack.toml ./agent.toml
  mkdir -p "$VAR_BASE_PATH"
  sed_inplace "s/port = 8120/port = ${ETCD_PORT}/" ./agent.toml
  sed_inplace "s/port = 6001/port = ${AGENT_RPC_PORT}/" ./agent.toml
  sed_inplace "s/port = 6009/port = ${AGENT_WATCHER_PORT}/" ./agent.toml
  sed_inplace "s@\(# \)\{0,1\}ipc-base-path = .*@ipc-base-path = "'"'"${IPC_BASE_PATH}"'"'"@" ./agent.toml
  sed_inplace "s@\(# \)\{0,1\}var-base-path = .*@var-base-path = "'"'"${VAR_BASE_PATH}"'"'"@" ./agent.toml

  # configure backend mode
  if [ $AGENT_BACKEND = "k8s" ] || [ $AGENT_BACKEND = "kubernetes" ]; then
    sed_inplace "s/mode = \"docker\"/mode = \"kubernetes\"/" ./agent.toml
    sed_inplace "s/scratch-type = \"hostdir\"/scratch-type = \"k8s-nfs\"/" ./agent.toml
  elif [ $AGENT_BACKEND = "docker" ]; then
    sed '/scratch-nfs-/d' ./agent.toml > ./agent.toml.sed
    mv ./agent.toml.sed ./agent.toml
  fi
  sed_inplace "s@\(# \)\{0,1\}mount-path = .*@mount-path = "'"'"${ROOT_PATH}/${VFOLDER_REL_PATH}"'"'"@" ./agent.toml
  if [ $ENABLE_CUDA -eq 1 ]; then
    sed_inplace "s/# allow-compute-plugins =.*/allow-compute-plugins = [\"ai.backend.accelerator.cuda_open\"]/" ./agent.toml
  elif [ $ENABLE_CUDA_MOCK -eq 1 ]; then
    sed_inplace "s/# allow-compute-plugins =.*/allow-compute-plugins = [\"ai.backend.accelerator.mock\"]/" ./agent.toml
  else
    sed_inplace "s/# allow-compute-plugins =.*/allow-compute-plugins = []/" ./agent.toml
  fi

  # configure agent
  cp configs/agent/sample-dummy-config.toml ./agent.dummy.toml

  # configure storage-proxy
  cp configs/storage-proxy/sample.toml ./storage-proxy.toml
  STORAGE_PROXY_RANDOM_KEY=$(python -c 'import secrets; print(secrets.token_hex(32), end="")')
  sed_inplace "s/port = 2379/port = ${ETCD_PORT}/" ./storage-proxy.toml
  sed_inplace "s/secret = \"some-secret-private-for-storage-proxy\"/secret = \"${STORAGE_PROXY_RANDOM_KEY}\"/" ./storage-proxy.toml
  sed_inplace "s/secret = \"some-secret-shared-with-manager\"/secret = \"${MANAGER_AUTH_KEY}\"/" ./storage-proxy.toml
  sed_inplace "s@\(# \)\{0,1\}ipc-base-path = .*@ipc-base-path = "'"'"${IPC_BASE_PATH}"'"'"@" ./storage-proxy.toml
  # comment out all sample volumes
  sed_inplace "s/^\[volume\./# \[volume\./" ./storage-proxy.toml
  sed_inplace "s/^backend =/# backend =/" ./storage-proxy.toml
  sed_inplace "s/^path =/# path =/" ./storage-proxy.toml
  sed_inplace "s/^purity/# purity/" ./storage-proxy.toml
  sed_inplace "s/^netapp_/# netapp_/" ./storage-proxy.toml
  sed_inplace "s/^weka_/# weka_/" ./storage-proxy.toml
  sed_inplace "s/^gpfs_/# gpfs_/" ./storage-proxy.toml
  sed_inplace "s/^vast_/# vast_/" ./storage-proxy.toml
  # add LOCAL_STORAGE_VOLUME vfs volume
  echo "\n[volume.${LOCAL_STORAGE_VOLUME}]\nbackend = \"vfs\"\npath = \"${ROOT_PATH}/${VFOLDER_REL_PATH}\"" >> ./storage-proxy.toml

  # configure webserver
  cp configs/webserver/halfstack.conf ./webserver.conf
  sed_inplace "s/https:\/\/api.backend.ai/http:\/\/127.0.0.1:${MANAGER_PORT}/" ./webserver.conf

  # configure wsproxy
  cp configs/wsproxy/halfstack.toml ./wsproxy.toml

  if [ $CONFIGURE_HA -eq 1 ]; then
    sed_inplace "s/redis.addr = \"localhost:6379\"/# redis.addr = \"localhost:6379\"/" ./webserver.conf
    sed_inplace "s/# redis.password = \"mysecret\"/redis.password = \"develove\"/" ./webserver.conf
    sed_inplace "s/# redis.service_name = \"mymaster\"/redis.service_name = \"mymaster\"/" ./webserver.conf
    sed_inplace "s/# redis.sentinel = \"127.0.0.1:9503,127.0.0.1:9504,127.0.0.1:9505\"/redis.sentinel = \"127.0.0.1:9503,127.0.0.1:9504,127.0.0.1:9505\"/ " ./webserver.conf
  else
    sed_inplace "s/redis.addr = \"localhost:6379\"/redis.addr = \"localhost:${REDIS_PORT}\"/" ./webserver.conf
  fi

  # install and configure webui
  if [ $EDITABLE_WEBUI -eq 1 ]; then
    install_editable_webui
    sed_inplace "s@\(#\)\{0,1\}static_path = .*@static_path = "'"src/ai/backend/webui/build/rollup"'"@" ./webserver.conf
  else
    webui_version=$(jq -r '.package + " (built at " + .buildDate + ", rev " + .revision + ")"' src/ai/backend/web/static/version.json)
    show_note "The currently embedded webui version: $webui_version"
  fi

  if [ "${CODESPACES}" = "true" ]; then
    $docker_sudo docker stop $($docker_sudo docker ps -q)
    $docker_sudo docker compose -f "docker-compose.halfstack.current.yml" down
    $docker_sudo docker compose -f "docker-compose.halfstack.current.yml" up -d
  fi

  # initialize the DB schema
  show_info "Setting up databases..."
  ./backend.ai mgr schema oneshot
  ./backend.ai mgr fixture populate fixtures/manager/example-users.json
  ./backend.ai mgr fixture populate fixtures/manager/example-keypairs.json
  ./backend.ai mgr fixture populate fixtures/manager/example-set-user-main-access-keys.json
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
  ./backend.ai mgr image rescan cr.backend.ai
  if [ "$(uname -m)" = "arm64" ] || [ "$(uname -m)" = "aarch64" ]; then
    ./backend.ai mgr image alias python "cr.backend.ai/multiarch/python:3.9-ubuntu20.04" aarch64
  else
    ./backend.ai mgr image alias python "cr.backend.ai/stable/python:3.9-ubuntu20.04" x86_64
  fi

  # Virtual folder setup
  VFOLDER_VERSION="3"
  VFOLDER_VERSION_TXT="version.txt"
  show_info "Setting up virtual folder..."
  mkdir -p "${ROOT_PATH}/${VFOLDER_REL_PATH}"
  echo "${VFOLDER_VERSION}" > "${ROOT_PATH}/${VFOLDER_REL_PATH}/${VFOLDER_VERSION_TXT}"
  ./backend.ai mgr etcd put-json volumes "./dev.etcd.volumes.json"
  mkdir -p scratches
  POSTGRES_CONTAINER_ID=$($docker_sudo docker compose -f "docker-compose.halfstack.current.yml" ps | grep "[-_]backendai-half-db[-_]1" | awk '{print $1}')
  ALL_VFOLDER_HOST_PERM='["create-vfolder","modify-vfolder","delete-vfolder","mount-in-session","upload-file","download-file","invite-others","set-user-specific-permission"]'
  $docker_sudo docker exec -it $POSTGRES_CONTAINER_ID psql postgres://postgres:develove@localhost:5432/backend database -c "update domains set allowed_vfolder_hosts = '{\"${LOCAL_STORAGE_PROXY}:${LOCAL_STORAGE_VOLUME}\": ${ALL_VFOLDER_HOST_PERM}}';"
  $docker_sudo docker exec -it $POSTGRES_CONTAINER_ID psql postgres://postgres:develove@localhost:5432/backend database -c "update groups set allowed_vfolder_hosts = '{\"${LOCAL_STORAGE_PROXY}:${LOCAL_STORAGE_VOLUME}\": ${ALL_VFOLDER_HOST_PERM}}';"
  $docker_sudo docker exec -it $POSTGRES_CONTAINER_ID psql postgres://postgres:develove@localhost:5432/backend database -c "update keypair_resource_policies set allowed_vfolder_hosts = '{\"${LOCAL_STORAGE_PROXY}:${LOCAL_STORAGE_VOLUME}\": ${ALL_VFOLDER_HOST_PERM}}';"
  $docker_sudo docker exec -it $POSTGRES_CONTAINER_ID psql postgres://postgres:develove@localhost:5432/backend database -c "update vfolders set host = '${LOCAL_STORAGE_PROXY}:${LOCAL_STORAGE_VOLUME}' where host='${LOCAL_STORAGE_VOLUME}';"

  # Client backend endpoint configuration shell script
  CLIENT_ADMIN_CONF_FOR_API="env-local-admin-api.sh"
  CLIENT_ADMIN_CONF_FOR_SESSION="env-local-admin-session.sh"
  echo "# Directly access to the manager using API keypair (admin)" > "${CLIENT_ADMIN_CONF_FOR_API}"
  echo "export BACKEND_ENDPOINT=http://127.0.0.1:${MANAGER_PORT}/" >> "${CLIENT_ADMIN_CONF_FOR_API}"
  echo "export BACKEND_ACCESS_KEY=$(cat fixtures/manager/example-keypairs.json | jq -r '.keypairs[] | select(.user_id=="admin@lablup.com") | .access_key')" >> "${CLIENT_ADMIN_CONF_FOR_API}"
  echo "export BACKEND_SECRET_KEY=$(cat fixtures/manager/example-keypairs.json | jq -r '.keypairs[] | select(.user_id=="admin@lablup.com") | .secret_key')" >> "${CLIENT_ADMIN_CONF_FOR_API}"
  echo "export BACKEND_ENDPOINT_TYPE=api" >> "${CLIENT_ADMIN_CONF_FOR_API}"
  chmod +x "${CLIENT_ADMIN_CONF_FOR_API}"
  echo "# Indirectly access to the manager via the web server using a cookie-based login session (admin)" > "${CLIENT_ADMIN_CONF_FOR_SESSION}"
  echo "export BACKEND_ENDPOINT=http://127.0.0.1:${WEBSERVER_PORT}" >> "${CLIENT_ADMIN_CONF_FOR_SESSION}"

  case $(basename $SHELL) in
    fish)
        echo "set -e BACKEND_ACCESS_KEY" >> "${CLIENT_ADMIN_CONF_FOR_SESSION}"
        echo "set -e BACKEND_SECRET_KEY" >> "${CLIENT_ADMIN_CONF_FOR_SESSION}"
    ;;
    *)
        echo "unset BACKEND_ACCESS_KEY" >> "${CLIENT_ADMIN_CONF_FOR_SESSION}"
        echo "unset BACKEND_SECRET_KEY" >> "${CLIENT_ADMIN_CONF_FOR_SESSION}"
    ;;
  esac

  echo "export BACKEND_ENDPOINT_TYPE=session" >> "${CLIENT_ADMIN_CONF_FOR_SESSION}"
  echo "echo 'Run backend.ai login to make an active session.'" >> "${CLIENT_ADMIN_CONF_FOR_SESSION}"
  echo "echo 'Username: $(cat fixtures/manager/example-users.json | jq -r '.users[] | select(.username=="admin") | .email')'" >> "${CLIENT_ADMIN_CONF_FOR_SESSION}"
  echo "echo 'Password: $(cat fixtures/manager/example-users.json | jq -r '.users[] | select(.username=="admin") | .password')'" >> "${CLIENT_ADMIN_CONF_FOR_SESSION}"
  chmod +x "${CLIENT_ADMIN_CONF_FOR_SESSION}"
  CLIENT_DOMAINADMIN_CONF_FOR_API="env-local-domainadmin-api.sh"
  CLIENT_DOMAINADMIN_CONF_FOR_SESSION="env-local-domainadmin-session.sh"
  echo "# Directly access to the manager using API keypair (admin)" > "${CLIENT_DOMAINADMIN_CONF_FOR_API}"
  echo "export BACKEND_ENDPOINT=http://127.0.0.1:${MANAGER_PORT}/" >> "${CLIENT_DOMAINADMIN_CONF_FOR_API}"
  echo "export BACKEND_ACCESS_KEY=$(cat fixtures/manager/example-keypairs.json | jq -r '.keypairs[] | select(.user_id=="domain-admin@lablup.com") | .access_key')" >> "${CLIENT_DOMAINADMIN_CONF_FOR_API}"
  echo "export BACKEND_SECRET_KEY=$(cat fixtures/manager/example-keypairs.json | jq -r '.keypairs[] | select(.user_id=="domain-admin@lablup.com") | .secret_key')" >> "${CLIENT_DOMAINADMIN_CONF_FOR_API}"
  echo "export BACKEND_ENDPOINT_TYPE=api" >> "${CLIENT_DOMAINADMIN_CONF_FOR_API}"
  chmod +x "${CLIENT_DOMAINADMIN_CONF_FOR_API}"
  echo "# Indirectly access to the manager via the web server using a cookie-based login session (admin)" > "${CLIENT_DOMAINADMIN_CONF_FOR_SESSION}"
  echo "export BACKEND_ENDPOINT=http://127.0.0.1:${WEBSERVER_PORT}" >> "${CLIENT_DOMAINADMIN_CONF_FOR_SESSION}"

  case $(basename $SHELL) in
    fish)
        echo "set -e BACKEND_ACCESS_KEY" >> "${CLIENT_DOMAINADMIN_CONF_FOR_SESSION}"
        echo "set -e BACKEND_SECRET_KEY" >> "${CLIENT_DOMAINADMIN_CONF_FOR_SESSION}"
    ;;
    *)
        echo "unset BACKEND_ACCESS_KEY" >> "${CLIENT_DOMAINADMIN_CONF_FOR_SESSION}"
        echo "unset BACKEND_SECRET_KEY" >> "${CLIENT_DOMAINADMIN_CONF_FOR_SESSION}"
    ;;
  esac

  echo "export BACKEND_ENDPOINT_TYPE=session" >> "${CLIENT_DOMAINADMIN_CONF_FOR_SESSION}"
  echo "echo 'Run backend.ai login to make an active session.'" >> "${CLIENT_DOMAINADMIN_CONF_FOR_SESSION}"
  echo "echo 'Username: $(cat fixtures/manager/example-users.json | jq -r '.users[] | select(.username=="domain-admin") | .email')'" >> "${CLIENT_DOMAINADMIN_CONF_FOR_SESSION}"
  echo "echo 'Password: $(cat fixtures/manager/example-users.json | jq -r '.users[] | select(.username=="domain-admin") | .password')'" >> "${CLIENT_DOMAINADMIN_CONF_FOR_SESSION}"
  chmod +x "${CLIENT_DOMAINADMIN_CONF_FOR_SESSION}"
  CLIENT_USER_CONF_FOR_API="env-local-user-api.sh"
  CLIENT_USER_CONF_FOR_SESSION="env-local-user-session.sh"
  echo "# Directly access to the manager using API keypair (user)" > "${CLIENT_USER_CONF_FOR_API}"
  echo "export BACKEND_ENDPOINT=http://127.0.0.1:${MANAGER_PORT}/" >> "${CLIENT_USER_CONF_FOR_API}"
  echo "export BACKEND_ACCESS_KEY=$(cat fixtures/manager/example-keypairs.json | jq -r '.keypairs[] | select(.user_id=="user@lablup.com") | .access_key')" >> "${CLIENT_USER_CONF_FOR_API}"
  echo "export BACKEND_SECRET_KEY=$(cat fixtures/manager/example-keypairs.json | jq -r '.keypairs[] | select(.user_id=="user@lablup.com") | .secret_key')" >> "${CLIENT_USER_CONF_FOR_API}"
  echo "export BACKEND_ENDPOINT_TYPE=api" >> "${CLIENT_USER_CONF_FOR_API}"
  chmod +x "${CLIENT_USER_CONF_FOR_API}"
  CLIENT_USER2_CONF_FOR_API="env-local-user2-api.sh"
  CLIENT_USER2_CONF_FOR_SESSION="env-local-user2-session.sh"
  echo "# Directly access to the manager using API keypair (user2)" > "${CLIENT_USER2_CONF_FOR_API}"
  echo "export BACKEND_ENDPOINT=http://127.0.0.1:${MANAGER_PORT}/" >> "${CLIENT_USER2_CONF_FOR_API}"
  echo "export BACKEND_ACCESS_KEY=$(cat fixtures/manager/example-keypairs.json | jq -r '.keypairs[] | select(.user_id=="user2@lablup.com") | .access_key')" >> "${CLIENT_USER2_CONF_FOR_API}"
  echo "export BACKEND_SECRET_KEY=$(cat fixtures/manager/example-keypairs.json | jq -r '.keypairs[] | select(.user_id=="user2@lablup.com") | .secret_key')" >> "${CLIENT_USER2_CONF_FOR_API}"
  echo "export BACKEND_ENDPOINT_TYPE=api" >> "${CLIENT_USER2_CONF_FOR_API}"
  chmod +x "${CLIENT_USER2_CONF_FOR_API}"
  echo "# Indirectly access to the manager via the web server using a cookie-based login session (user)" > "${CLIENT_USER_CONF_FOR_SESSION}"
  echo "export BACKEND_ENDPOINT=http://127.0.0.1:${WEBSERVER_PORT}" >> "${CLIENT_USER_CONF_FOR_SESSION}"

  case $(basename $SHELL) in
    fish)
        echo "set -e BACKEND_ACCESS_KEY" >> "${CLIENT_USER_CONF_FOR_SESSION}"
        echo "set -e BACKEND_SECRET_KEY" >> "${CLIENT_USER_CONF_FOR_SESSION}"
    ;;
    *)
        echo "unset BACKEND_ACCESS_KEY" >> "${CLIENT_USER_CONF_FOR_SESSION}"
        echo "unset BACKEND_SECRET_KEY" >> "${CLIENT_USER_CONF_FOR_SESSION}"
    ;;
  esac

  echo "export BACKEND_ENDPOINT_TYPE=session" >> "${CLIENT_USER_CONF_FOR_SESSION}"
  echo "echo 'Run backend.ai login to make an active session.'" >> "${CLIENT_USER_CONF_FOR_SESSION}"
  echo "echo 'Username: $(cat fixtures/manager/example-users.json | jq -r '.users[] | select(.username=="user") | .email')'" >> "${CLIENT_USER_CONF_FOR_SESSION}"
  echo "echo 'Password: $(cat fixtures/manager/example-users.json | jq -r '.users[] | select(.username=="user") | .password')'" >> "${CLIENT_USER_CONF_FOR_SESSION}"
  chmod +x "${CLIENT_USER_CONF_FOR_SESSION}"

  show_info "Dumping the installed etcd configuration to ./dev.etcd.installed.json as a backup."
  ./backend.ai mgr etcd get --prefix '' > ./dev.etcd.installed.json

  show_info "Installation finished."
  echo "${GREEN}Development environment is now ready.${NC}"

  # TODO: Automate the following steps
  if [ $CONFIGURE_HA -eq 1 ]; then
    echo "${RED}[NOTE] Please add the following lines to \"/etc/hosts\" file in your host OS.${NC}"
    echo "${RED}127.0.0.1 node01${NC}"
    echo "${RED}127.0.0.1 node02${NC}"
    echo "${RED}127.0.0.1 node03${NC}"
  fi
}

if [ $CODESPACES != "true" ] || [ $CODESPACES_ON_CREATE -eq 1 ]; then
  setup_environment
fi
if [ $CODESPACES != "true" ] || [ $CODESPACES_POST_CREATE -eq 1 ]; then
  configure_backendai
  show_guide
fi
# vim: tw=0 sts=2 sw=2 et
