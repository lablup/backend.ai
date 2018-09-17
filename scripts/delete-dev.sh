#! /bin/bash

readlinkf() {
  python -c "import os,sys; print(os.path.realpath(os.path.expanduser(sys.argv[1])))" "${1}"
}

usage() {
  echo "Backend.AI Development Setup - Auto-removal Tool"
  echo "================================================"
  echo ""
  echo "Usage: $0 [OPTIONS]"
  echo ""
  echo "OPTIONS                DESCRIPTION"
  echo "  -h, --help           Show this help"
  echo "  -e, --env            Set the target environment ID (required)"
  echo "  --install-path       Set the target directory"
  echo "                       (default: ./backend.ai-dev)"
  echo "  --remove-venvs       Whether to remove virtualenvs"
  echo "                       (default: yes)"
  echo "  --remove-containers  Whether to remove docker resources"
  echo "                       (default: yes)"
  echo "  --remove-source      Whether to remove cloned source directories"
  echo "                       (default: yes)"
}

normalize_bool() {
  local arg=$(echo $1 | tr '[:upper:]' '[:lower:]')
  case "$arg" in
    y | yes | t | true | 1)  echo "yes" ;;
    n | no | f | false | 0)  echo "no" ;;
    *)
      echo "Invalid boolean option: $1"
      exit 1
  esac
}

ENV_ID=""
INSTALL_PATH="./backend.ai-dev"
REMOVE_VENVS="yes"
REMOVE_CONTAINERS="yes"
REMOVE_SOURCE="yes"

while [ $# -gt 0 ]; do
  case $1 in
    -h | --help)           usage; exit 1 ;;
    --install-path)        INSTALL_PATH=$2; shift ;;
    --install-path=*)      INSTALL_PATH="${1#*=}" ;;
    --remove-venvs)        REMOVE_VENVS=$(normalize_bool $2); shift ;;
    --remove-venvs=*)      REMOVE_VENVS=$(normalize_bool "${1#*=}") ;;
    --remove-containers)   REMOVE_CONTAINERS=$(normalize_bool $2); shift ;;
    --remove-containers=*) REMOVE_CONTAINERS=$(normalize_bool "${1#*=}") ;;
    --remove-source)       REMOVE_SOURCE=$(normalize_bool $2); shift ;;
    --remove-source=*)     REMOVE_SOURCE=$(normalize_bool "${1#*=}") ;;
    -e | --env)            ENV_ID=$2; shift ;;
    --env=*)               ENV_ID="${1#*=}" ;;
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

if [ "$REMOVE_VENVS" = "yes" ]; then
  echo "Removing Python virtual environments..."
  pyenv uninstall -f "venv-${ENV_ID}-agent"
  pyenv uninstall -f "venv-${ENV_ID}-client"
  pyenv uninstall -f "venv-${ENV_ID}-common"
  pyenv uninstall -f "venv-${ENV_ID}-manager"
else
  echo "Skipped removal of Python virtual environments."
fi

if [ "$REMOVE_CONTAINERS" = "yes" ]; then
  echo "Removing Docker containers..."
  cd "${INSTALL_PATH}/backend.ai"
  docker-compose -p "${ENV_ID}" -f docker-compose.halfstack.yml down
else
  echo "Skipped removal of Docker containers."
fi

if [ "$REMOVE_SOURCE" = "yes" ]; then
  echo "Removing cloned source files..."
  sudo rm -rf "${INSTALL_PATH}"
else
  echo "Skipped removal of cloned source files."
fi
echo "Done."
