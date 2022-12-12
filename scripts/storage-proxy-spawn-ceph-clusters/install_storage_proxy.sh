#!/bin/sh

cd $HOME/
sudo apt update
sudo apt-get install -y build-essential git-core libreadline-dev libsqlite3-dev libssl-dev libbz2-dev tk-dev libzmq3-dev libsnappy-dev libffi-dev zlib1g-dev wget curl llvm libncursesw5-dev xz-utils  libxml2-dev libxmlsec1-dev  liblzma-dev

curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
apt-get install docker-compose
sudo usermod -aG docker ${USER}
sudo gpasswd -a vagrant docker
su -s ${USER}


curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source "$HOME/.cargo/env"

git clone https://github.com/lablup/backend.ai bai-dev
cd bai-dev
./scripts/install-dev.sh

sudo apt-get -y install ceph-fuse
sudo apt-get -y install attr
sudo chmod 775 ceph.conf
sudo mkdir /mnt/vfroot/ceph-fuse/ -p
sudo ceph-fuse -n client.admin --keyring=/etc/ceph/ceph.client.admin.keyring  -m ceph-server-1 /mnt/vfroot/ceph-fuse/ &
python -m ai.backend.storage.server &
exit
