#! /bin/bash
export GITHUB_TOKEN=$MY_GITHUB_TOKEN
git config --global credential.helper=/.codespaces/bin/gitcredential_github.sh

# Install pyenv
read -r -d '' pyenv_init_script <<"EOS"
export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"
eval "$(pyenv virtualenv-init -)"
EOS
if ! type "pyenv" >/dev/null 2>&1; then
  show_info "Installing pyenv..."
  set -e
  curl https://pyenv.run | sh
  for PROFILE_FILE in "zshrc" "bashrc" "profile" "bash_profile"
  do
    if [ -e "${HOME}/.${PROFILE_FILE}" ]
    then
      echo "$pyenv_init_script" >> "${HOME}/.${PROFILE_FILE}"
    fi
  done
  set +e
  eval "$pyenv_init_script"
  pyenv
else
  eval "$pyenv_init_script"
fi

sed -i 's/^git clone.*backend\.ai$//g' /workspaces/backend.ai/scripts/install-dev.sh
bash /workspaces/backend.ai/scripts/install-dev.sh --install-path /workspaces