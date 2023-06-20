#!/bin/sh
sudo chmod 755 /
echo "StrictHostKeyChecking no" >> .ssh/config
mkdir test-cluster && cd test-cluster/

ssh-keyscan 192.168.56.10 192.168.56.11 192.168.56.12 192.168.56.13 192.168.56.14
ssh-keyscan ceph-admin ceph-server-1 ceph-server-2 ceph-server-3 ceph-client

yes | ceph-deploy new ceph-server-1 ceph-server-2 ceph-server-3
yes | ceph-deploy install --release=octopus ceph-admin ceph-server-1 ceph-server-2 ceph-server-3 ceph-client

ceph-deploy mon create-initial
ssh ceph-server-2 "sudo mkdir /var/local/osd0 && sudo chown ceph:ceph /var/local/osd0"
ssh ceph-server-3 "sudo mkdir /var/local/osd1 && sudo chown ceph:ceph /var/local/osd1"

ceph-deploy osd prepare ceph-server-2:/var/local/osd0 ceph-server-3:/var/local/osd1
ceph-deploy osd activate ceph-server-2:/var/local/osd0 ceph-server-3:/var/local/osd1

yes | ceph-deploy admin ceph-admin ceph-server-1 ceph-server-2 ceph-server-3 ceph-client
sudo chmod +r /etc/ceph/ceph.client.admin.keyring
ssh ceph-server-1 sudo chmod +r /etc/ceph/ceph.client.admin.keyring
ssh ceph-server-2 sudo chmod +r /etc/ceph/ceph.client.admin.keyring
ssh ceph-server-3 sudo chmod +r /etc/ceph/ceph.client.admin.keyring
ssh ceph-client   sudo chmod +r /etc/ceph/ceph.client.admin.keyring

ceph-deploy mgr create ceph-admin:mon_mgr
ceph-deploy mds create ceph-server-1
ceph osd pool create rbd 150 150

# Creates pool for metadata
ceph osd pool create cephfs_metadata 30 30
# Creates pool for filesystem data
ceph osd pool create cephfs 30 30
# Creates Filesystem
ceph fs new test_fs cephfs_metadata cephfs
sudo apt-get -y install ceph-fuse
ceph fs authorize test_fs client.foo / rwp
echo "Done"
exit
