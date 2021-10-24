#! /bin/bash

if [ -e "/workspaces/manager" ] 
then 
  exit 0
fi

GITHUB_TOKEN=${CUSTOM_GITHUB_TOKEN:-$GITHUB_TOKEN}
for PROFILE_FILE in "zshrc" "bashrc" "profile" "bash_profile"
do
  if [ -e "${HOME}/.${PROFILE_FILE}" ]
  then
    echo "export GITHUB_TOKEN=${GITHUB_TOKEN}" >> "${HOME}/.${PROFILE_FILE}"
  fi
done

export GITHUB_TOKEN=$GITHUB_TOKEN

git config --global credential.helper=/.codespaces/bin/gitcredential_github.sh

cp /workspaces/backend.ai/scripts/install-dev.sh /tmp/install-backend-ai.sh

sed -i '/pyenv init --path/ a  eval "$(pyenv init -)"' /tmp/install-backend-ai.sh
sed -i 's/^git clone.*backend\.ai$//g' /tmp/install-backend-ai.sh

bash /tmp/install-backend-ai.sh --install-path /workspaces -e codespaces >install.log 2>&1 
