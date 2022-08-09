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
  echo "  ${LWHITE}-h, --help${NC}         Show this help and exit"
  echo ""
  echo "  ${LWHITE}--skip-containers${NC}  Skip removal of docker resources (default: false)"
  echo ""
  echo "  ${LWHITE}--skip-venvs${NC}       Skip removal of temporary virtualenvs (default: false)"
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

INSTALL_PATH="./backend.ai-dev"
REMOVE_VENVS=1
REMOVE_CONTAINERS=1

while [ $# -gt 0 ]; do
  case $1 in
    -h | --help)           usage; exit 1 ;;
    --skip-venvs)          REMOVE_VENVS=0 ;;
    --skip-containers)     REMOVE_CONTAINERS=0 ;;
    *)
      echo "Unknown option: $1"
      echo "Run '$0 --help' for usage."
      exit 1
  esac
  shift 1
done

if [ $REMOVE_VENVS -eq 1 ]; then
  echo "Removing the unified and temporary venvs..."
  rm -rf dist/export
  pyenv uninstall -f "tmp-grpcio-build"
else
  echo "Skipped removal of Python virtual environments."
fi

if [ $REMOVE_CONTAINERS -eq 1 ]; then
  echo "Removing Docker containers..."
  $docker_sudo $DOCKER_COMPOSE -f "docker-compose.halfstack.current.yml" down
  rm "docker-compose.halfstack.current.yml"
else
  echo "Skipped removal of Docker containers."
fi

echo ""
echo "(FYI) To reset Pants and its cache data, run:"
echo "  $ killall pantsd"
echo "  $ rm -r .tmp .pants.d .pants.env pants-local ~/.cache/pants"

echo ""
echo "Done."
