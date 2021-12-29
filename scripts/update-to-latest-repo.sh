#!/bin/bash

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
REWRITELN="\033[A\r\033[K"

echo "${LGREEN}Backend-ai: Update-to-latest-repo ${NC}"

read -e -p "Enter Your BRANCH_VERSION:" -i "main" BRANCH_VERSION
echo "${YELLOW}${BRANCH_VERSION}${NC}"

read -e -p "Enter Your INSTALL_PATH:" -i "./backend.ai-dev" INSTALL_PATH
echo "${YELLOW}${INSTALL_PATH}${NC}"

cd ${INSTALL_PATH}
pwd

for dir in backend.ai
do
  echo ${d}
  if [ ! -d "$dir" ]; then
      echo "${RED} There is no ${dir} directory ${NC}"
      continue
  fi
  cd ${dir}
  git checkout ${BRANCH_VERSION}
  pip install --upgrade pip
  git fetch
  git pull
  cd ..
done

for dir in common
do
  if [ ! -d "$dir" ]; then
      echo "${RED} There is no ${d} directory ${NC}"
      continue
  fi
  cd ${dir}
  git checkout ${BRANCH_VERSION}
  pip install --upgrade pip
  git fetch
  git pull
  pip install -U -r ./requirements/dev.txt
  cd ..
done

for dir in agent storage-proxy client-py manager
do
  if [ ! -d "$dir" ]; then
      echo "${RED} There is no ${d} directory ${NC}"
      continue
  fi
  cd ${dir}
  git checkout ${BRANCH_VERSION}
  pip install --upgrade pip
  git fetch
  git pull
  pip install -U -r ./requirements/dev.txt
  pip install -U -e ../common
  cd ..
done

for dir in webserver
do
    if [ ! -d "$dir" ]; then
        echo "${RED} There is no ${d} directory ${NC}"
        continue
    fi
    cd ${dir}
    pip install -U pip
    pip install -U -e .
    pip install -U -e ../client-py
    cd ..
done

for dir in manager
do
    if [ ! -d "$dir" ]; then
        echo "${RED} There is no ${d} directory ${NC}"
        continue
    fi
    cd ${dir}
    alembic upgrade head
done
