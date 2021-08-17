#! /bin/bash
export GITHUB_TOKEN=$MY_GITHUB_TOKEN
git config --global credential.helper=/.codespaces/bin/gitcredential_github.sh

sed -i 's/^git clone.*backend\.ai$//g' /workspaces/backend.ai/scripts/install-dev.sh
bash /workspaces/backend.ai/scripts/install-dev.sh --install-path /workspaces > install.log
