#! /bin/bash
export GITHUB_TOKEN=$MY_GITHUB_TOKEN
for PROFILE_FILE in "zshrc" "bashrc" "profile" "bash_profile"
do
  if [ -e "${HOME}/.${PROFILE_FILE}" ]
  then
    echo "export GITHUB_TOKEN=$MY_GITHUB_TOKEN" >> "${HOME}/.${PROFILE_FILE}"
  fi
done

git config --global credential.helper=/.codespaces/bin/gitcredential_github.sh

export

sed -i '/pyenv init --path/ a  eval "$(pyenv init -)"' /workspaces/backend.ai/scripts/install-dev.sh
sed -i 's/^git clone.*backend\.ai$//g' /workspaces/backend.ai/scripts/install-dev.sh

bash /workspaces/backend.ai/scripts/install-dev.sh --install-path /workspaces >install.log 2>&1 
