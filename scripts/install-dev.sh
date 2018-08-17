#!/bin/sh
# Pre-setup
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
LRED='\033[1;31m'
LGREEN='\033[1;32m'
LBLUE='\033[1;34m'
LG='\033[0;37m'
NC='\033[0m'

ROOT_PATH=${PWD}
# Make directories
echo " "
echo "${LGREEN}Backend.AI one-line installer for developers"
echo " "

# Check prerequistics
if ! type "docker" > /dev/null; then
    echo " "
    echo "${RED}[ERROR]${NC} ${LRED}You need docker install backend.ai environment.${NC}"
    echo " "
    echo "${BLUE}[INFO]${NC} ${GREEN}Install latest docker before starting installation.${NC}"
    cd ${ROOT_PATH}
    exit 0
fi

echo "${BLUE}[INFO]${NC} ${GREEN}Creating backend.ai-dev directory...${NC}"
mkdir -p backend.ai-dev
cd backend.ai-dev
INSTALL_PATH=${PWD}

# Install postgresql, etcd packages via  docker
git clone https://github.com/lablup/backend.ai
cd backend.ai
docker-compose -f docker-compose.halfstack.yml up -d
docker ps # You should see three containers here.

# install pyenv
if ! type "pyenv" > /dev/null; then
    echo "${BLUE}[INFO]${NC} ${GREEN}Installing pyenv...${NC}"
    git clone https://github.com/pyenv/pyenv.git ${HOME}/.pyenv
    git clone https://github.com/pyenv/pyenv-virtualenv.git ${HOME}/.pyenv/plugins/pyenv-virtualenv
    for PROFILE_FILE in "zshrc" "bashrc" "profile"
    do
        if [ -e "${HOME}/.${PROFILE_FILE}" ]
        then
            echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ${HOME}/.${PROFILE_FILE}
            echo 'export PATH="$PYENV_ROOT/bin:$PATH"' >> ${HOME}/.${PROFILE_FILE}
            echo 'eval "$(pyenv init -)"' >> ${HOME}/.${PROFILE_FILE}
            echo 'eval "$(pyenv virtualenv-init -)"' >> ${HOME}/.${PROFILE_FILE}
            exec $SHELL -l
        fi
    done
    pyenv
fi

# Install python to pyenv environment
echo "${BLUE}[INFO]${NC} ${GREEN}Creating virtualenv on pyenv...${NC}"
pyenv install -s 3.6.6
pyenv virtualenv 3.6.6 venv-manager
pyenv virtualenv 3.6.6 venv-agent
pyenv virtualenv 3.6.6 venv-common
pyenv virtualenv 3.6.6 venv-client

# Clone source codes
echo "${BLUE}[INFO]${NC} ${GREEN}Cloning backend.ai source codes...${NC}"
cd ${INSTALL_PATH}
git clone https://github.com/lablup/backend.ai-manager
git clone https://github.com/lablup/backend.ai-agent
git clone https://github.com/lablup/backend.ai-common

# Setup virtual environments
cd ${INSTALL_PATH}/backend.ai-manager
if [[ "$OSTYPE" == "linux-gnu" ]]; then
    if [ $(python -c "from ctypes.util import find_library;print(find_library('snappy'))") = "None" ]; then
        echo " "
        echo "${RED}[ERROR]${NC} ${LRED}You need snappy library to install backend.ai components.${NC}"
        echo " "
        echo "${BLUE}[INFO]${NC} ${GREEN}Install libsnappy-dev (Debian-likes), or libsnappy-devel (RHEL-likes) system package depending on your environment.${NC}"
        cd ${ROOT_PATH}
        exit 0
    fi
fi

echo "${BLUE}[INFO]${NC} ${GREEN}Install packages on virtual environments...${NC}"
cd ${INSTALL_PATH}/backend.ai-manager
pyenv local venv-manager
pip install -U -r requirements-dev.txt

cd ${INSTALL_PATH}/backend.ai-agent
pyenv local venv-agent
pip install -U -r requirements-dev.txt

cd ${INSTALL_PATH}/backend.ai-common
pyenv local venv-common
pip install -U -r requirements-dev.txt

# Make symlink to current backend.ai-common source code from other modules
echo "${BLUE}[INFO]${NC} ${GREEN}Linking package dependency between sources...${NC}"

cd "$(pyenv prefix venv-manager)/src"
mv backend.ai-common backend.ai-common-backup
ln -s "${INSTALL_PATH}/backend.ai-common" backend.ai-common

cd "$(pyenv prefix venv-agent)/src"
mv backend.ai-common backend.ai-common-backup
ln -s "${INSTALL_PATH}/backend.ai-common" backend.ai-common

# Manager DB setup
echo "${BLUE}[INFO]${NC} ${GREEN}Setup databases / images...${NC}"
cd ${INSTALL_PATH}/backend.ai-manager
cp sample-configs/image-metadata.yml image-metadata.yml
cp sample-configs/image-aliases.yml image-aliases.yml
./scripts/run-with-halfstack.sh python -m ai.backend.manager.cli etcd update-images -f image-metadata.yml
./scripts/run-with-halfstack.sh python -m ai.backend.manager.cli etcd update-aliases -f image-aliases.yml

# Virtual folder setup
echo "${BLUE}[INFO]${NC} ${GREEN}Setup virtual folder...${NC}"
mkdir -p ${INSTALL_PATH}/vfolder
./scripts/run-with-halfstack.sh python -m ai.backend.manager.cli etcd put volumes/_vfroot ${INSTALL_PATH}/vfolder
cd ${INSTALL_PATH}/backend.ai-agent
mkdir -p scratches

# DB schema
echo "${BLUE}[INFO]${NC} ${GREEN}Setup databases / images...${NC}"
cd ${INSTALL_PATH}/backend.ai-manager
cp alembic.ini.sample alembic.ini
python -m ai.backend.manager.cli schema oneshot head
python -m ai.backend.manager.cli --db-addr=localhost:8100 --db-user=postgres --db-password=develove --db-name=backend fixture populate example_keypair

echo "${BLUE}[INFO]${NC} ${GREEN}Install Python client SDK/CLI source...${NC}"
cd ${INSTALL_PATH}
# Install python client package
git clone https://github.com/lablup/backend.ai-client-py
cd ${INSTALL_PATH}/backend.ai-client-py
pyenv local venv-client
pip install -U -r requirements-dev.txt

echo "${BLUE}[INFO]${NC} ${GREEN}Downloading python runtime for backend.ai...${NC}"
docker pull lablup/kernel-python:3.6-debian

cd ${INSTALL_PATH}
echo " "
echo "${GREEN}Installation finished.${NC}"
echo " "
echo "${BLUE}[NOTE]${NC} Default API keypair configuration for test / develop:"
echo "> export BACKEND_ENDPOINT=http://127.0.0.1:8081/"
echo "> export BACKEND_ACCESS_KEY=AKIAIOSFODNN7EXAMPLE"
echo "> export BACKEND_SECRET_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
echo " "
echo "Please add these environment variables to your shell configuration files."
echo "${LRED}[NOTE]${NC} You should change your default admin API keypairs for production environment!"
echo " "
echo "${BLUE}[NOTE]${NC} How to run Backend.AI manager:"
echo "> cd ${INSTALL_PATH}/backend.ai-manager"
echo "> ./scripts/run-with-halfstack.sh python -m ai.backend.gateway.server --service-port=8081 --debug"
echo " "
echo "${BLUE}[NOTE]${NC} How to run Backend.AI agent:"
echo "> cd ${INSTALL_PATH}/backend.ai-agent"
echo "> ./scripts/run-with-halfstack.sh python -m ai.backend.agent.server --scratch-root=`pwd`/scratches --debug --idle-timeout 30"
echo " "
echo "${BLUE}[NOTE]${NC} How to run your first code:"
echo "> cd ${INSTALL_PATH}/backend.ai-client-py"
echo "> backend.ai run python -c \"print('Hello World!')\""
echo " "
echo "${BLUE}[NOTE]${NC} type 'backend.ai' for more commands."
echo " "
echo "${GREEN}Development environment prepared.${NC}"
echo " "
