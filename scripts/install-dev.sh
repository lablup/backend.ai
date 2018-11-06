#! /bin/bash

# Set "echo -e" as default
shopt -s xpg_echo

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

readlinkf() {
  $bpython -c "import os,sys; print(os.path.realpath(os.path.expanduser(sys.argv[1])))" "${1}"
}

trim() {
  echo "$1" | sed -e 's/^[[:space:]]*//g' -e 's/[[:space:]]*$//g'
}

usage() {
  echo "${GREEN}Backend.AI Development Setup${NC}: ${CYAN}Auto-installer Tool${NC}"
  echo ""
  echo "${LWHITE}USAGE${NC}"
  echo "  $0 ${LWHITE}[OPTIONS]${NC}"
  echo ""
  echo "${LWHITE}OPTIONS${NC}"
  echo "  ${LWHITE}-h, --help${NC}           Show this help message and exit"
  echo ""
  echo "  ${LWHITE}--python-version VERSION${NC}"
  echo "                       Set the Python version to install via pyenv"
  echo "                       (default: 3.6.6)"
  echo ""
  echo "  ${LWHITE}--install-path PATH${NC}  Set the target directory"
  echo "                       (default: ./backend.ai-dev)"
  echo ""
  echo "  ${LWHITE}--server-branch NAME${NC}"
  echo "                       The branch of git clones for server components"
  echo "                       (default: master)"
  echo ""
  echo "  ${LWHITE}--client-branch NAME${NC}"
  echo "                       The branch of git clones for client components"
  echo "                       (default: master)"
  echo ""
  echo "  ${LWHITE}--enable-cuda${NC}        Install CUDA accelerator plugin and pull a"
  echo "                       TenosrFlow CUDA kernel for testing/demo."
  echo "                       (default: false)"
  echo ""
  echo "  ${LWHITE}--cuda-branch NAME${NC}   The branch of git clone for the CUDA accelerator "
  echo "                       plugin; only valid if ${LWHITE}--enable-cuda${NC} is specified."
  echo "                       (default: master)"
}

show_error() {
  echo " "
  echo "${RED}[ERROR]${NC} ${LRED}$1${NC}"
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
if [ $(has_python "python") -eq 1 ]; then
  bpython=$(which "python")
elif [ $(has_python "python3") -eq 1 ]; then
  bpython=$(which "python3")
elif [ $(has_python "python2") -eq 1 ]; then
  bpython=$(which "python2")
else
  # Ensure "readlinkf" is working...
  show_error "python (for bootstrapping) is not available!"
  show_info "This script assumes Python 2.7+/3+ is already available on your system."
  exit 1
fi

ROOT_PATH=$(pwd)
PYTHON_VERSION="3.6.6"
SERVER_BRANCH="master"
CLIENT_BRANCH="master"
INSTALL_PATH="./backend.ai-dev"
ENABLE_CUDA=0
CUDA_BRANCH="master"

while [ $# -gt 0 ]; do
  case $1 in
    -h | --help)        usage; exit 1 ;;
    --python-version)   PYTHON_VERSION=$2; shift ;;
    --python-version=*) PYTHON_VERSION="${1#*=}" ;;
    --install-path)     INSTALL_PATH=$2; shift ;;
    --install-path=*)   INSTALL_PATH="${1#*=}" ;;
    --server-branch)    SERVER_BRANCH=$2; shift ;;
    --server-branch=*)  SERVER_BRANCH="${1#*=}" ;;
    --client-branch)    CLIENT_BRANCH=$2; shift ;;
    --client-branch=*)  CLIENT_BRANCH="${1#*=}" ;;
    --enable-cuda)      ENABLE_CUDA=1 ;;
    --cuda-branch)      CUDA_BRANCH=$2; shift ;;
    --cuda-branch=*)    CUDA_BRANCH="${1#*=}" ;;
    *)
      echo "Unknown option: $1"
      echo "Run '$0 --help' for usage."
      exit 1
  esac
  shift
done
INSTALL_PATH=$(readlinkf "$INSTALL_PATH")

install_script_deps() {
  case $DISTRO in
  Debian)
    $sudo apt-get update
    $sudo apt-get install -y git
    ;;
  RedHat)
    $sudo yum clean expire-cache  # next yum invocation will update package metadata cache
    $sudo yum install -y git
    ;;
  Darwin)
    if ! type "brew" >/dev/null 2>&1; then
      show_error "brew is not available!"
      show_info "Sorry, we only support auto-install on macOS using Homebrew. Please install it and try again."
      exit 1
    fi
    brew update
    # Having Homebrew means that the user already has git.
    ;;
  esac
}

install_pybuild_deps() {
  case $DISTRO in
  Debian)
    $sudo apt-get install -y libssl-dev libreadline-dev libgdbm-dev zlib1g-dev libbz2-dev libsqlite3-dev libffi-dev
    ;;
  RedHat)
    $sudo yum install -y openssl-devel readline-devel gdbm-devel zlib-devel bzip2-devel libsqlite-devel libffi-devel
    ;;
  Darwin)
    brew bundle --file=- <<"EOS"
brew "openssl"
brew "sqlite3"
brew "readline"
brew "zlib"
brew "gdbm"
brew "tcl-tk"
EOS
    ;;
  esac
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
    brew bundle --file=- <<EOS
brew "$3"
EOS
  esac
}

# BEGIN!

echo " "
echo "${LGREEN}Backend.AI one-line installer for developers${NC}"

# NOTE: docker-compose enforces lower-cased project names
ENV_ID=$(LC_ALL=C tr -dc 'a-z0-9' < /dev/urandom | head -c 8)

# Check prerequisites
show_info "Checking prerequisites and script dependencies..."
install_script_deps
if ! type "docker" >/dev/null 2>&1; then
  show_error "docker is not available!"
  show_info "Please install the latest version of docker and try again."
  show_info "Visit https://docs.docker.com/install/ for instructions."
  exit 1
fi
if ! type "docker-compose" >/dev/null 2>&1; then
  show_error "docker-compose is not available!"
  show_info "Please install the latest version of docker-compose and try again."
  show_info "Visit https://docs.docker.com/compose/install/ for instructions."
  exit 1
fi

# Install pyenv
read -r -d '' pyenv_init_script <<"EOS"
export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"
eval "$(pyenv virtualenv-init -)"
EOS
if ! type "pyenv" >/dev/null 2>&1; then
  # TODO: ask if install pyenv
  show_info "Installing pyenv..."
  set -e
  git clone https://github.com/pyenv/pyenv.git "${HOME}/.pyenv"
  git clone https://github.com/pyenv/pyenv-virtualenv.git "${HOME}/.pyenv/plugins/pyenv-virtualenv"
  for PROFILE_FILE in "zshrc" "bashrc" "profile" "bash_profile"
  do
    if [ -e "${HOME}/.${PROFILE_FILE}" ]
    then
      echo "$pyenv_init_script" >> "${HOME}/.${PROFILE_FILE}"
      eval "$pyenv_init_script"
    fi
  done
  set +e
  pyenv
fi

# Install Python and pyenv virtualenvs
show_info "Checking and installing Python dependencies..."
install_pybuild_deps

show_info "Installing Python..."
if [ "$DISTRO" = "Darwin" ]; then
  export PYTHON_CONFIGURE_OPTS="--enable-framework --with-tcl-tk"
  export CFLAGS="-I$(brew --prefix openssl)/include -I$(brew --prefix sqlite3)/include -I$(brew --prefix readline)/include -I$(brew --prefix zlib)/include -I$(brew --prefix gdbm)/include -I$(brew --prefix tcl-tk)/include"
  export LDFLAGS="-L$(brew --prefix openssl)/lib -L$(brew --prefix sqlite3)/lib -L$(brew --prefix readline)/lib -L$(brew --prefix zlib)/lib -L$(brew --prefix gdbm)/lib -L$(brew --prefix tcl-tk)/lib"
fi
if [ -z "$(pyenv versions | grep -E "^[[:space:]]*${PYTHON_VERSION}$")" ]; then
  pyenv install "${PYTHON_VERSION}"
else
  echo "${PYTHON_VERSION} is already installed."
fi
if [ "$DISTRO" = "Darwin" ]; then
  unset PYTHON_CONFIGURE_OPTS
  unset CFLAGS
  unset LDFLAGS
fi

show_info "Creating virtualenv on pyenv..."
pyenv virtualenv "${PYTHON_VERSION}" "venv-${ENV_ID}-manager"
pyenv virtualenv "${PYTHON_VERSION}" "venv-${ENV_ID}-agent"
pyenv virtualenv "${PYTHON_VERSION}" "venv-${ENV_ID}-common"
pyenv virtualenv "${PYTHON_VERSION}" "venv-${ENV_ID}-client"

# Make directories
show_info "Creating the install directory..."
mkdir -p "${INSTALL_PATH}"
cd "${INSTALL_PATH}"

# Install postgresql, etcd packages via docker
show_info "Launching the docker-compose \"halfstack\"..."
git clone --branch "${SERVER_BRANCH}" https://github.com/lablup/backend.ai
cd backend.ai
$docker_sudo docker-compose -f docker-compose.halfstack.yml -p "${ENV_ID}" up -d
$docker_sudo docker ps | grep "${ENV_ID}"   # You should see three containers here.

# Clone source codes
show_info "Cloning backend.ai source codes..."
cd "${INSTALL_PATH}"
git clone --branch "${SERVER_BRANCH}" https://github.com/lablup/backend.ai-manager manager
git clone --branch "${SERVER_BRANCH}" https://github.com/lablup/backend.ai-agent agent
git clone --branch "${SERVER_BRANCH}" https://github.com/lablup/backend.ai-common common
if [ $ENABLE_CUDA -eq 1 ]; then
  git clone --branch "${CUDA_BRANCH}" https://github.com/lablup/backend.ai-accelerator-cuda accel-cuda
fi

check_snappy() {
  pip download python-snappy
  local pkgfile=$(ls | grep snappy)
  if [[ $pkgfile =~ .*\.tar.gz ]]; then
    # source build is required!
    install_system_pkg "libsnappy-dev" "libsnappy-devel" "snappy"
  fi
  rm -f $pkgfile
}

show_info "Install packages on virtual environments..."
cd "${INSTALL_PATH}/manager"
pyenv local "venv-${ENV_ID}-manager"
check_snappy
pip install -U -q pip setuptools
pip install -U -e ../common -r requirements-dev.txt

cd "${INSTALL_PATH}/agent"
pyenv local "venv-${ENV_ID}-agent"
pip install -U -q pip setuptools
pip install -U -e ../common -r requirements-dev.txt
if [[ "$OSTYPE" == "linux-gnu" ]]; then
  $sudo setcap cap_sys_ptrace,cap_sys_admin,cap_dac_override+eip $(readlinkf $(pyenv which python))
fi
if [ $ENABLE_CUDA -eq 1 ]; then
  cd "${INSTALL_PATH}/accel-cuda"
  pyenv local "venv-${ENV_ID}-agent"  # share the agent's venv
  pip install -U -e .
fi

cd "${INSTALL_PATH}/common"
pyenv local "venv-${ENV_ID}-common"
pip install -U -q pip setuptools
pip install -U -r requirements-dev.txt

# Manager DB setup
show_info "Configuring kernel images..."
cd "${INSTALL_PATH}/manager"
cp sample-configs/image-metadata.yml image-metadata.yml
cp sample-configs/image-aliases.yml image-aliases.yml
./scripts/run-with-halfstack.sh python -m ai.backend.manager.cli etcd update-images -f image-metadata.yml
./scripts/run-with-halfstack.sh python -m ai.backend.manager.cli etcd update-aliases -f image-aliases.yml

# Virtual folder setup
show_info "Setting up virtual folder..."
mkdir -p "${INSTALL_PATH}/vfolder/local"
./scripts/run-with-halfstack.sh python -m ai.backend.manager.cli etcd put volumes/_mount "${INSTALL_PATH}/vfolder"
./scripts/run-with-halfstack.sh python -m ai.backend.manager.cli etcd put volumes/_default_host "local"
cd "${INSTALL_PATH}/agent"
mkdir -p scratches

# DB schema
show_info "Setting up databases..."
cd "${INSTALL_PATH}/manager"
cp alembic.ini.sample alembic.ini
python -m ai.backend.manager.cli schema oneshot head
python -m ai.backend.manager.cli --db-addr=localhost:8100 --db-user=postgres --db-password=develove --db-name=backend fixture populate example_keypair

show_info "Installing Python client SDK/CLI source..."
cd "${INSTALL_PATH}"
# Install python client package
git clone --branch "${CLIENT_BRANCH}" https://github.com/lablup/backend.ai-client-py client-py
cd "${INSTALL_PATH}/client-py"
pyenv local "venv-${ENV_ID}-client"
pip install -U -q pip setuptools
pip install -U -r requirements-dev.txt

show_info "Downloading Python kernel images for Backend.AI..."
$docker_sudo docker pull lablup/kernel-python:3.6-debian
$docker_sudo docker pull lablup/kernel-python-tensorflow:1.11-py36
if [ $ENABLE_CUDA -eq 1 ]; then
  $docker_sudo docker pull lablup/kernel-python-tensorflow:1.11-py36-gpu
fi

DELETE_OPTS=''
if [ ! "$INSTALL_PATH" = $(readlinkf "./backend.ai-dev") ]; then
  DELETE_OPTS+=" --install-path=${INSTALL_PATH}"
fi
DELETE_OPTS=$(trim "$DELETE_OPTS")

cd "${INSTALL_PATH}"
show_info "Installation finished."
show_note "Default API keypair configuration for test / develop:"
echo "> ${WHITE}export BACKEND_ENDPOINT=http://127.0.0.1:8081/${NC}"
echo "> ${WHITE}export BACKEND_ACCESS_KEY=AKIAIOSFODNN7EXAMPLE${NC}"
echo "> ${WHITE}export BACKEND_SECRET_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY${NC}"
echo " "
echo "Please add these environment variables to your shell configuration files."
show_important_note "You should change your default admin API keypairs for production environment!"
show_note "How to run Backend.AI manager:"
echo "> ${WHITE}cd ${INSTALL_PATH}/manager${NC}"
echo "> ${WHITE}./scripts/run-with-halfstack.sh python -m ai.backend.gateway.server --service-port=8081 --debug${NC}"
show_note "How to run Backend.AI agent:"
echo "> ${WHITE}cd ${INSTALL_PATH}/agent${NC}"
echo "> ${WHITE}./scripts/run-with-halfstack.sh python -m ai.backend.agent.server --scratch-root=\$(pwd)/scratches --debug --idle-timeout 30${NC}"
show_note "How to run your first code:"
echo "> ${WHITE}cd ${INSTALL_PATH}/client-py${NC}"
echo "> ${WHITE}backend.ai --help${NC}"
echo "> ${WHITE}backend.ai run python -c \"print('Hello World!')\"${NC}"
echo " "
echo "${GREEN}Development environment is now ready.${NC}"
show_note "Your environment ID is ${YELLOW}${ENV_ID}${NC}."
echo "  * When using docker-compose, do:"
echo "    > ${WHITE}cd ${INSTALL_PATH}/manager${NC}"
if [ ! -z "$docker_sudo" ]; then
  echo "    > ${WHITE}${docker_sudo} docker-compose -p ${ENV_ID} -f docker-compose.halfstack.yml ...${NC}"
else
  echo "    > ${WHITE}docker-compose -p ${ENV_ID} -f docker-compose.halfstack.yml ...${NC}"
fi
echo "  * To delete this development environment, run:"
echo "    > ${WHITE}$(dirname $0)/delete-dev.sh --env ${ENV_ID} ${DELETE_OPTS}${NC}"
echo " "
