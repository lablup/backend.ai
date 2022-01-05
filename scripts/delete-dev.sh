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

usage() {
  echo "${GREEN}Backend.AI Development Setup${NC}: ${CYAN}Auto-removal Tool${NC}"
  echo ""
  echo "${LWHITE}USAGE${NC}"
  echo "  $0 ${LWHITE}[OPTIONS]${NC}"
  echo ""
  echo "${LWHITE}OPTIONS${NC}"
  echo "  ${LWHITE}-h, --help${NC}           Show this help and exit"
  echo ""
  echo "  ${LWHITE}-e, --env ENVID${NC}      Set the target environment ID (required)"
  echo ""
  echo "  ${LWHITE}--install-path PATH${NC}  Set the target directory when installed in a"
  echo "                       non-default locatin (default: ./backend.ai-dev)"
  echo ""
  echo "  ${LWHITE}--skip-venvs${NC}         Skip removal of virtualenvs (default: false)"
  echo ""
  echo "  ${LWHITE}--skip-containers${NC}    Skip removal of docker resources (default: false)"
  echo ""
  echo "  ${LWHITE}--skip-source${NC}        Skip removal of the install path (default: false)"
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

docker compose version >/dev/null 2>&1
if [ $? -eq 0 ]; then
  DOCKER_COMPOSE="docker compose"
else
  DOCKER_COMPOSE="docker-compose"
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

ENV_ID=""
INSTALL_PATH="./backend.ai-dev"
REMOVE_VENVS=1
REMOVE_CONTAINERS=1
REMOVE_SOURCE=1

while [ $# -gt 0 ]; do
  case $1 in
    -h | --help)           usage; exit 1 ;;
    -e | --env)            ENV_ID=$2; shift ;;
    --env=*)               ENV_ID="${1#*=}" ;;
    --install-path)        INSTALL_PATH=$2; shift ;;
    --install-path=*)      INSTALL_PATH="${1#*=}" ;;
    --skip-venvs)          REMOVE_VENVS=0 ;;
    --skip-containers)     REMOVE_CONTAINERS=0 ;;
    --skip-source)         REMOVE_SOURCE=0 ;;
    *)
      echo "Unknown option: $1"
      echo "Run '$0 --help' for usage."
      exit 1
  esac
  shift 1
done
if [ -z "$ENV_ID" ]; then
  echo "You must specify the environment ID (-e/--env option)"
  exit 1
fi
INSTALL_PATH=$(readlinkf "$INSTALL_PATH")

if [ $REMOVE_VENVS -eq 1 ]; then
  echo "Removing Python virtual environments..."
  pyenv uninstall -f "venv-${ENV_ID}-agent"
  pyenv uninstall -f "venv-${ENV_ID}-client"
  pyenv uninstall -f "venv-${ENV_ID}-common"
  pyenv uninstall -f "venv-${ENV_ID}-manager"
  pyenv uninstall -f "venv-${ENV_ID}-webserver"
  pyenv uninstall -f "venv-${ENV_ID}-storage-proxy"
else
  echo "Skipped removal of Python virtual environments."
fi

if [ $REMOVE_CONTAINERS -eq 1 ]; then
  echo "Removing Docker containers..."
  cd "${INSTALL_PATH}/backend.ai"
  $docker_sudo $DOCKER_COMPOSE -p "${ENV_ID}" -f "docker-compose.halfstack.${ENV_ID}.yml" down
  rm "docker-compose.halfstack.${ENV_ID}.yml"
else
  echo "Skipped removal of Docker containers."
fi

if [ $REMOVE_SOURCE -eq 1 ]; then
  echo "Removing cloned source files..."
  $sudo rm -rf "${INSTALL_PATH}/manager"
  $sudo rm -rf "${INSTALL_PATH}/agent"
  $sudo rm -rf "${INSTALL_PATH}/common"
  $sudo rm -rf "${INSTALL_PATH}/client-py"
  $sudo rm -rf "${INSTALL_PATH}/webserver"
  $sudo rm -rf "${INSTALL_PATH}/storage-proxy"
  $sudo rm -rf "${INSTALL_PATH}/backend.ai"
  $sudo rm -rf "${INSTALL_PATH}/vfolder"
  $sudo rm -rf "${INSTALL_PATH}/accel-cuda"
  echo "Please remove ${INSTALL_PATH} by yourself."
else
  echo "Skipped removal of cloned source files."
fi
echo "Done."
