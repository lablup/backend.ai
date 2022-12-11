#! /bin/bash
set -euo pipefail
shopt -s xpg_echo

# NOTE: this script should be executed from the repository root.

# Color constants
RED="\033[0;91m"
YELLOW="\033[0;93m"
GREEN="\033[0;92m"
CYAN="\033[0;96m"
WHITE="\033[0;97m"
LWHITE="\033[1;37m"
NC="\033[0m"

function join_by { local IFS="$1"; shift; echo "$*"; }

HALFSTACK_VOLUME_PATH="$(pwd)/volumes"
DOCKER_COMPOSE_CURRENT="docker-compose.halfstack.current.yml"
DOCKER_COMPOSE_MAIN="docker-compose.halfstack-main.yml"

function upgrade() {
  echo "${CYAN}▪ [halfstack]${WHITE} Environment${NC}"
  echo " - HALFSTACK_VOLUME_PATH = ${HALFSTACK_VOLUME_PATH}"
  echo " - DOCKER_COMPOSE_CURRENT = ${DOCKER_COMPOSE_CURRENT} (will be used as the source of configurations)"
  echo " - DOCKER_COMPOSE_MAIN = ${DOCKER_COMPOSE_MAIN} (will be used as the template for the new halfstack)"
  echo
  echo -n "${WHITE}Do you want to proceed? [Y/n]${NC} "; read -n 1 -r
  if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 1
  fi
  echo

  # NOTE: etcd and redis does not require explicit migration procedures.
  echo "${GREEN}✓ [redis]${WHITE} Redis does not require explicit migration.${NC}"
  echo "${GREEN}✓ [etcd]${WHITE} etcd does not require explicit migration within th 3.x series.${NC}"

  POSTGRES_CONTAINER=$(docker compose -f ${DOCKER_COMPOSE_CURRENT} ps -q "backendai-half-db")
  POSTGRES_OLD_VERSION=$(cat "${DOCKER_COMPOSE_CURRENT}" | yq '.services."backendai-half-db".image')
  POSTGRES_NEW_VERSION=$(cat "${DOCKER_COMPOSE_MAIN}" | yq '.services."backendai-half-db".image')
  if [ "$POSTGRES_OLD_VERSION" == "$POSTGRES_NEW_VERSION" ]; then
    echo "${GREEN}✓ [postgres]${WHITE} The postgres container version has not been changed. Skipping upgrade.${NC}"
  else
    echo "${CYAN}▪ [postgres]${WHITE} Upgrading postgres from ${POSTGRES_OLD_VERSION} ($(echo ${POSTGRES_CONTAINER} | cut -b -12)) to ${POSTGRES_NEW_VERSION}"

    echo "${CYAN}▪ [postgres]${WHITE} Making the database dump at ${HALFSTACK_VOLUME_PATH}/postgres-data.old/upgrade-dump.{schema,data}.sql ...${NC}"
    docker exec -it ${POSTGRES_CONTAINER} sh -c 'pg_dumpall --schema-only -U postgres --database=backend > /var/lib/postgresql/data/upgrade-dump.schema.sql'
    docker exec -it ${POSTGRES_CONTAINER} sh -c 'pg_dumpall --data-only -U postgres --database=backend > /var/lib/postgresql/data/upgrade-dump.data.sql'

    echo "${CYAN}▪ [halfstack]${WHITE} Stopping the current halfstack ...${NC}"
    docker compose -f "${DOCKER_COMPOSE_CURRENT}" down
    echo "${CYAN}▪ [postgres]${WHITE} Migrating the database to the new version of postgres ...${NC}"
    sudo mv "${HALFSTACK_VOLUME_PATH}/postgres-data" "${HALFSTACK_VOLUME_PATH}/postgres-data.old"
    sudo mkdir -p "${HALFSTACK_VOLUME_PATH}/postgres-data"
    sudo docker pull "${POSTGRES_NEW_VERSION}"
    local current_db_envs=($(cat ${DOCKER_COMPOSE_CURRENT} | yq '.services."backendai-half-db".environment.[]'))
    TEMP_CID=$(sudo docker run -d \
      -v ${HALFSTACK_VOLUME_PATH}/postgres-data.old:/data.old \
      -v ${HALFSTACK_VOLUME_PATH}/postgres-data:/var/lib/postgresql/data \
      $(join_by ' ' ${current_db_envs[@]/#/-e }) \
      "${POSTGRES_NEW_VERSION}")
    while :
    do
      { sudo docker exec -it ${TEMP_CID} sh -c 'pg_isready -U postgres >/dev/null 2>&1'; rc=$?; } || :
      if [ $rc -eq 0 ]; then break; fi
      sleep 0.5
    done
    echo "${YELLOW}▪ [postgres]${WHITE} NOTE: It is safe to ignore some 'already exists' errors.${NC}"
    sudo docker exec -it ${TEMP_CID} sh -c 'psql -U postgres -f /data.old/upgrade-dump.schema.sql >/dev/null'
    sudo docker exec -it ${TEMP_CID} sh -c 'psql -U postgres -f /data.old/upgrade-dump.data.sql >/dev/null'
    sudo docker stop ${TEMP_CID} && sudo docker rm ${TEMP_CID}
  fi

  echo "${CYAN}▪ [halfstack]${WHITE} Updating ${DOCKER_COMPOSE_CURRENT} ...${NC}"
  cp "${DOCKER_COMPOSE_CURRENT}" "${DOCKER_COMPOSE_CURRENT}.backup"
  # assuming that each port config has only one line...
  postgres_ports=$(cat "${DOCKER_COMPOSE_CURRENT}" | yq '.services."backendai-half-db".ports.[]')
  redis_ports=$(cat "${DOCKER_COMPOSE_CURRENT}" | yq '.services."backendai-half-redis".ports.[]')
  etcd_ports=$(cat "${DOCKER_COMPOSE_CURRENT}" | yq '.services."backendai-half-etcd".ports.[]')
  cp "${DOCKER_COMPOSE_MAIN}" "${DOCKER_COMPOSE_CURRENT}"
  yq -i '.services."backendai-half-db".ports = [''"'"$postgres_ports"'"]' ${DOCKER_COMPOSE_CURRENT}
  yq -i '.services."backendai-half-redis".ports = [''"'"$redis_ports"'"]' ${DOCKER_COMPOSE_CURRENT}
  yq -i '.services."backendai-half-etcd".ports = [''"'"$etcd_ports"'"]' ${DOCKER_COMPOSE_CURRENT}

  echo "${CYAN}▪ [halfstack]${WHITE} Recreating the docker compose stack ...${NC}"
  docker compose -f "${DOCKER_COMPOSE_CURRENT}" up -d

  echo "${GREEN}✓ [halfstack]${WHITE} Completed upgrade.${NC}"
  exit 0
}

function revert() {
  echo "${RED}▪ [halfstack]${WHITE} WARNING: Any database changes after the upgrade will be lost.${NC}"
  echo
  echo -n "${WHITE}Are you sure to continue? [y/n]${NC} "
  read -n 1 -r
  if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 1
  fi
  echo
  echo "${CYAN}▪ [halfstack]${WHITE} Shutting down the compose stack ...${NC}"
  docker compose -f docker-compose.halfstack.current.yml down
  echo "${CYAN}▪ [halfstack]${WHITE} Purging the postgres-data dircetory generated in the newer version ...${NC}"
  sudo rm -r volumes/postgres-data
  sudo mv volumes/postgres-data.old volumes/postgres-data
  echo "${CYAN}▪ [halfstack]${WHITE} Restoring ${DOCKER_COMPOSE_CURRENT} from ${DOCKER_COMPOSE_CURRENT}.backup ...${NC}"
  cp docker-compose.halfstack.current.yml.backup docker-compose.halfstack.current.yml
  echo "${CYAN}▪ [halfstack]${WHITE} Recreating the compose stack ...${NC}"
  docker compose -f docker-compose.halfstack.current.yml up -d
  echo "${GREEN}✓ [halfstack]${WHITE} Completed revert.${NC}"
  exit 0
}

function usage() {
  echo "${LWHITE}USAGE${NC}"
  echo "  $0 ${LWHITE}[OPTIONS]${NC}"
  echo
  echo "${LWHITE}OPTIONS${NC}"
  echo "  ${LWHITE}-h, --help${NC}"
  echo "    Show this help message and exit"
  echo
  echo "  ${LWHITE}--revert${NC}"
  echo "    Perform the revert of the last upgrade."
  echo "    Note that this will loose any database updates after the upgrade."
}

while [ $# -gt 0 ]; do
  case $1 in
    -h | --help)   usage; exit 1 ;;
    --revert)      revert; shift ;;
    *)
      echo "Unknown option: $1"
      echo "Run '$0 --help' for usage."
      exit 1
  esac
  shift
done

upgrade
