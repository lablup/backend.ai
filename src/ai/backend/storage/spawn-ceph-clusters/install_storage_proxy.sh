#!/bin/sh


sudo chmod 755 /
cd $HOME/

sudo apt install -y python3.8

sudo apt-get install -y build-essential git-core libreadline-dev libsqlite3-dev libssl-dev libbz2-dev tk-dev libzmq3-dev libsnappy-dev libffi-dev

sudo git clone https://github.com/pyenv/pyenv.git "$HOME/.pyenv"
echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.profile
echo 'export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.profile
echo 'eval "$(pyenv init -)"' >> ~/.profile

echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bashrc
echo 'export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bashrc
echo 'eval "$(pyenv init -)"' >> ~/.bashrc

sudo git clone https://github.com/pyenv/pyenv-virtualenv.git "$HOME/.pyenv/plugins/pyenv-virtualenv"
echo 'eval "$(pyenv virtualenv-init -)"' >> ~/.profile
echo 'eval "$(pyenv virtualenv-init -)"' >> ~/.bashrs
sudo chmod 777 -R .pyenv/
eval "$(pyenv init -)"
eval "$(pyenv virtualenv-init -)"

pyenv install 3.9.4
pyenv virtualenv 3.9.4 storage-proxy
pyenv global storage-proxy
sudo git clone https://github.com/lablup/backend.ai-storage-agent /vagrant/storage-proxy/
cd /vagrant/storage-proxy/
pyenv local storage-proxy

python3.9 -m pip install --upgrade pip
pip install backend.ai-common
pip install -U -r requirements/dev.txt

sudo apt-get -y install ceph-fuse
sudo apt-get -y install attr

sudo mkdir /mnt/vfroot/ceph-fuse/ -p
sudo ceph-fuse -n client.admin --keyring=/etc/ceph/ceph.client.admin.keyring  -m ceph-server-1 /mnt/vfroot/ceph-fuse/ &
python -m ai.backend.storage.server &
exit
