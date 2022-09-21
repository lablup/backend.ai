# Readme


# Installation
1. Setup vagrant environment and vagrant machine nodes
 ```
 mkdir vagrant_box/
 cd vagrant_box
 vagrant plugin install vagrant-cachier
 vagrant plugin install vagrant-hostmanager
 ssh-add -K ~/.vagrant.d/insecure_private_key
 vagrant up
```
2. Login to ceph-admin node and execute ceph-deployment script

```
vagrant ssh ceph-admin
sh /vagrant/install_ceph.sh
exit
```

3. Login to ceph-client and install ceph-fuse and Storage Proxy.
The Storage proxy is installed at root /vagrant directory which is also shared with Host machine.
The ceph-fuse mounted path is /mnt/vfroot/ceph-fuse
Create storage-proxy.toml config file at the vagrant_box/ directory.
The storage-proxy.toml will contain updated path 
```
[volume.myceph]
backend="cephfs"
path="/mnt/vfroot/ceph-fuse"
```
Etcd IP address should be updated to proper one based on Host machine.

Next run ceph-fuse and installing proxy storage script on ceph-client

```
vagrant ssh ceph-client
sh /vagrant/install_storage_proxy.sh
```

4. Manager settings
In volume .json set the vagrant network ip address of ceph-client node.
```
backend.ai mgr etcd put-json volumes volume.json
update domains set allowed_vfolder_hosts = '{local:myceph}' ;
update groups set allowed_vfolder_hosts = '{local:myceph}' ;
update keypair_resource_policies set allowed_vfolder_hosts = '{local:myceph}' ;
```

# Mounting Ceph-Fuse
On ceph-client machine it is already mounted on install.
```
sudo ceph-fuse -n client.admin --keyring=/etc/ceph/ceph.client.admin.keyring  -m ceph-server-1 /mnt/vfroot/ceph-fuse/
```

# Setting Quotas setup
vagrant ssh ceps-admin
ceph fs authorize test_fs client.foo / rwp

Copy the key to the ceph-client at /etc/ceph/ceph.client.foo.keyring

At the ceph-client: mount the ceps-fuse with created client account.
```
sudo ceph-fuse -n client.foo --keyring=/etc/ceph/ceph.client.foo.keyring  -m ceph-server-1 /mnt/vfroot/ceph-fuse/
sudo mkdir /mnt/vfroot/ceph-fuse/test/
sudo setfattr -n ceph.quota.max_bytes -v 100000000 /mnt/vfroot/ceph-fuse/test/
getfattr -n ceph.quota.max_bytes /mnt/vfroot/ceph-fuse/test/
```
