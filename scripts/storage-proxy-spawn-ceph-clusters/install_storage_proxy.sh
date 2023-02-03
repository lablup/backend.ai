#!/bin/sh


sudo chmod 755 /
cd $HOME/
sudo apt update
sudo apt-get install -y build-essential git-core libreadline-dev libsqlite3-dev libssl-dev libbz2-dev tk-dev libzmq3-dev libffi-dev zlib1g-dev wget curl llvm libncursesw5-dev xz-utils  libxml2-dev libxmlsec1-dev  liblzma-dev

curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo apt-get install docker-compose
sudo addgroup docker
sudo adduser vagrant docker

sudo apt-get install git-lfs
git lfs install
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source "$HOME/.cargo/env"

curl https://pyenv.run | bash
export PYENV_ROOT="$HOME/.pyenv"
command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"
eval "$(pyenv virtualenv-init -)"

echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.profile
echo 'export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.profile
echo 'eval "$(pyenv init -)"' >> ~/.profile

echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bashrc
echo 'export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bashrc
echo 'eval "$(pyenv init -)"' >> ~/.bashrc

echo 'eval "$(pyenv virtualenv-init -)"' >> ~/.profile
echo 'eval "$(pyenv virtualenv-init -)"' >> ~/.bashrc

pyenv install 3.10.7
pyenv global 3.10.7
pyenv local 3.10.7

git clone https://github.com/lablup/backend.ai bai-dev
cd bai-dev
sudo ./scripts/install-dev.sh

sudo apt-get -y install ceph-fuse
sudo apt-get -y install attr

sudo mkdir /mnt/vfroot/ceph-fuse/ -p
sudo ceph-fuse -n client.admin --keyring=/etc/ceph/ceph.client.admin.keyring  -m ceph-server-1 /mnt/vfroot/ceph-fuse/ &
python -m ai.backend.storage.server &
exit
