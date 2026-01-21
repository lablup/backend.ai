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
  scripts/python.sh -c "import os,sys; print(os.path.realpath(os.path.expanduser(sys.argv[1])))" "${1}"
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
  echo ""
  echo "  ${LWHITE}--skip-db${NC}          Skip removal of volume resources (default: false)"
}

show_error() {
  echo " "
  echo "${RED}[ERROR]${NC} ${LRED}$1${NC}"
}

show_warning() {
  echo " "
  echo "${YELLOW}[WARN]${NC} ${LYELLOW}$1${NC}"
}

show_info() {
  echo " "
  echo "${BLUE}[INFO]${NC} ${GREEN}$1${NC}"
}

show_note() {
  echo " "
  echo "${BLUE}[NOTE]${NC} $1"
}

# Prepare sudo command options
ORIG_USER=${USER:-$(logname)}
if [[ "$OSTYPE" == "linux-gnu" ]]; then
  ORIG_HOME=$(getent passwd "$ORIG_USER" | cut -d: -f6)
  if [ $(id -u) = "0" ]; then
    docker_sudo=''
    sudo=''
  else
    docker_sudo="sudo HOME=${ORIG_HOME} PATH=${ORIG_HOME}/.local/bin:${PATH} -E --"
    sudo="sudo HOME=${ORIG_HOME} PATH=${ORIG_HOME}/.local/bin:${PATH} -E --"
  fi
elif [[ "$OSTYPE" == "darwin"* ]]; then
  ORIG_HOME=$(id -P "$ORIG_USER" | cut -d: -f9)
  if [ $(id -u) = "0" ]; then
    docker_sudo=''
    sudo=''
  else
    docker_sudo=''  # not required for docker commands (Docker Desktop, OrbStack, etc.)
    sudo="sudo HOME=${ORIG_HOME} PATH=${ORIG_HOME}/.local/bin:${PATH} -E --"
  fi
else
  echo "Unsupported OSTYPE: $OSTYPE"
  exit 1
fi

docker compose version >/dev/null 2>&1
if [ $? -eq 0 ]; then
  DOCKER_COMPOSE="docker compose"
else
  DOCKER_COMPOSE="docker-compose"
fi

INSTALL_PATH="./backend.ai-dev"
REMOVE_VENVS=1
REMOVE_CONTAINERS=1
REMOVE_DB=1

FORCE_YES=0
FORCE_NO=0

while [ $# -gt 0 ]; do
  case $1 in
    -h | --help)           usage; exit 1 ;;
    --skip-venvs)          REMOVE_VENVS=0 ;;
    --skip-containers)     REMOVE_CONTAINERS=0 ;;
    --skip-db)             REMOVE_DB=0 ;;
    -y | --yes)            FORCE_YES=1 ;;
    *)
      echo "Unknown option: $1"
      echo "Run '$0 --help' for usage."
      exit 1
  esac
  shift 1
done

# Confirm before deleting all resources
if [ $FORCE_YES -eq 1 ]; then
  show_info "Proceeding without confirmation (--yes flag)."
else
  echo ""
  echo -n "Are you sure you want to delete all development resources? [y/N]: "
  read -r confirm
  confirm=$(echo "$confirm" | tr '[:upper:]' '[:lower:]')
  if [ "$confirm" != "y" ] && [ "$confirm" != "yes" ]; then
    show_warning "Deletion cancelled."
    exit 0
  fi
fi

if [ $REMOVE_VENVS -eq 1 ]; then
  show_info "Removing the unified and temporary venvs..."
  rm -rf dist/export
  pyenv uninstall -f "tmp-grpcio-build"
else
  show_info "Skipped removal of Python virtual environments."
fi

if [ $REMOVE_CONTAINERS -eq 1 ]; then
  show_info "Removing Docker containers..."
  if [ -f "docker-compose.halfstack.current.yml" ]; then
    $docker_sudo $DOCKER_COMPOSE -f "docker-compose.halfstack.current.yml" down
    rm "docker-compose.halfstack.current.yml"
  else
    show_warning "The halfstack containers are already removed."
  fi
else
  show_info "Skipped removal of Docker containers."
fi

if [ $REMOVE_DB -eq 1 ]; then
  show_info "Removing data volumes..."
  rm -rf volumes
  docker volume rm $(docker volume ls -q --filter 'label=com.docker.compose.project=backendai')
fi

echo ""
show_note "(FYI) To reset Pants and its cache data, run:"
echo "  $ killall pantsd"
echo "  $ rm -rf .pants.d ~/.cache/pants"
if [ -f .pants.rc ]; then
  echo "  \$ rm -rf $(scripts/pyscript.sh scripts/tomltool.py -f .pants.rc get 'GLOBAL.local_execution_root_dir')"
fi

echo ""
show_info "Done."
