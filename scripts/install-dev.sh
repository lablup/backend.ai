#! /bin/bash

# Pre-setup
RED="\033[0;91m"
GREEN="\033[0;92m"
YELLOW="\033[0;93m"
BLUE="\033[0;94m"
WHITE="\033[0;97m"
LRED="\033[1;31m"
LGREEN="\033[1;32m"
LYELLOW="\033[1;33m"
LBLUE="\033[1;34m"
LWHITE="\033[1;37m"
LG="\033[0;37m"
NC="\033[0m"

# TODO: get from command arguments

PYTHON_VERSION="3.6.6"
ROOT_PATH=$(pwd)
INSTALL_PATH="$(pwd)/backend.ai-dev"

# Set "echo -e" as default
shopt -s xpg_echo

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


# BEGIN!

echo " "
echo "${LGREEN}Backend.AI one-line installer for developers${NC}"

# NOTE: docker-compose enforces lower-cased project names
ENV_ID=$(LC_CTYPE=C tr -dc 'a-z0-9' < /dev/urandom | head -c 8)

# Check prerequistics
if ! type "docker" > /dev/null; then
  show_error "docker is not available!"
  show_info "Install the latest version of docker and try again."
  exit 1
fi
if ! type "docker-compose" > /dev/null; then
  show_error "docker-compose is not available!"
  show_info "Install the latest version of docker-compose and try again."
  exit 1
fi

# Make directories
show_info "Creating backend.ai-dev directory..."
mkdir -p "${INSTALL_PATH}"
cd "${INSTALL_PATH}"

# Install postgresql, etcd packages via  docker
git clone https://github.com/lablup/backend.ai
cd backend.ai
docker-compose -f docker-compose.halfstack.yml -p "${ENV_ID}" up -d
docker ps | grep "${ENV_ID}"   # You should see three containers here.

# install pyenv
if ! type "pyenv" > /dev/null; then
  show_info "Installing pyenv..."
  git clone https://github.com/pyenv/pyenv.git "${HOME}/.pyenv"
  git clone https://github.com/pyenv/pyenv-virtualenv.git "${HOME}/.pyenv/plugins/pyenv-virtualenv"
  for PROFILE_FILE in "zshrc" "bashrc" "profile" "bash_profile"
  do
    if [ -e "${HOME}/.${PROFILE_FILE}" ]
    then
      echo 'export PYENV_ROOT="$HOME/.pyenv"' >> "${HOME}/.${PROFILE_FILE}"
      echo 'export PATH="$PYENV_ROOT/bin:$PATH"' >> "${HOME}/.${PROFILE_FILE}"
      echo 'eval "$(pyenv init -)"' >> "${HOME}/.${PROFILE_FILE}"
      echo 'eval "$(pyenv virtualenv-init -)"' >> ""${HOME}/.${PROFILE_FILE}
      exec "$SHELL" -l
    fi
  done
  pyenv
fi

# Install python to pyenv environment
show_info "Creating virtualenv on pyenv..."
pyenv install -s "${PYTHON_VERSION}"
pyenv virtualenv "${PYTHON_VERSION}" "venv-${ENV_ID}-manager"
pyenv virtualenv "${PYTHON_VERSION}" "venv-${ENV_ID}-agent"
pyenv virtualenv "${PYTHON_VERSION}" "venv-${ENV_ID}-common"
pyenv virtualenv "${PYTHON_VERSION}" "venv-${ENV_ID}-client"

# Clone source codes
show_info "Cloning backend.ai source codes..."
cd "${INSTALL_PATH}"
git clone https://github.com/lablup/backend.ai-manager manager
git clone https://github.com/lablup/backend.ai-agent agent
git clone https://github.com/lablup/backend.ai-common common

# Setup virtual environments
cd "${INSTALL_PATH}/manager"
if [[ "$OSTYPE" == "linux-gnu" ]]; then
    if [ $(python -c "from ctypes.util import find_library;print(find_library('snappy'))") = "None" ]; then
        show_error "You need snappy library to install backend.ai components."
        show_info "Install libsnappy-dev (Debian-likes), or libsnappy-devel (RHEL-likes) system package depending on your environment."
        cd ${ROOT_PATH}
        exit 1
    fi
    # NOTE: python-snappy 0.5.3 or later supports binary wheels on macOS.
fi

show_info "Install packages on virtual environments..."
cd "${INSTALL_PATH}/manager"
pyenv local "venv-${ENV_ID}-manager"
pip install -U -q pip setuptools
pip install -U -e ../common -r requirements-dev.txt

cd "${INSTALL_PATH}/agent"
pyenv local "venv-${ENV_ID}-agent"
pip install -U -q pip setuptools
pip install -U -e ../common -r requirements-dev.txt

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
mkdir -p "${INSTALL_PATH}/vfolder/azure-shard01"  # TODO: fix
./scripts/run-with-halfstack.sh python -m ai.backend.manager.cli etcd put volumes/_vfroot "${INSTALL_PATH}/vfolder"
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
git clone https://github.com/lablup/backend.ai-client-py client-py
cd "${INSTALL_PATH}/client-py"
pyenv local "venv-${ENV_ID}-client"
pip install -U -q pip setuptools
pip install -U -r requirements-dev.txt

show_info "Downloading Python kernel images for Backend.AI..."
docker pull lablup/kernel-python:3.6-debian
docker pull lablup/kernel-python-tensorflow:1.7-py36

cd "${INSTALL_PATH}"
echo " "
echo "${GREEN}Installation finished.${NC}"
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
echo "> ${WHITE}./scripts/run-with-halfstack.sh python -m ai.backend.agent.server --scratch-root=`pwd`/scratches --debug --idle-timeout 30${NC}"
show_note "How to run your first code:"
echo "> ${WHITE}cd ${INSTALL_PATH}/client-py${NC}"
echo "> ${WHITE}backend.ai --help${NC}"
echo "> ${WHITE}backend.ai run python -c \"print('Hello World!')\"${NC}"
echo " "
echo "${GREEN}Development environment is now ready.${NC}"
show_note "Your environment ID is ${YELLOW}${ENV_ID}${NC}."
echo "  * When using docker-compose, do:"
echo "    > ${WHITE}cd ${INSTALL_PATH}/manager${NC}"
echo "    > ${WHITE}docker-compose -p ${ENV_ID} -f docker-compose.halfstack.yml ...${NC}"
echo "  * To delete this development environment, run:"
echo "    > ${WHITE}./delete-dev.sh ${ENV_ID}${NC}"
echo " "
