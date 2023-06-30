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

Next run ceph-fuse and installing proxy storage script on ceph-client.

```
vagrant ssh ceph-client
sh /vagrant/install_storage_proxy.sh
```

4. Manager settings
In volume .json set the vagrant network ip address of ceph-client node if needed.
And add ceph volume configueations such as in example below.
```
[volume.myceph]
# An extended version for CephFS, which supports extended inode attributes
# for per-directory quota and fast metadata queries.
backend = "cephfs"
path = "/mnt/vfroot/ceph-fuse"
```

Example for volume.json could be
```
{
  "default_host": "local:myceph",
  "proxies": {
    "local": {
      "client_api": "http://127.0.0.1:6021",
      "manager_api": "https://127.0.0.1:6022",
      "secret": "77b651ec2fb9a5929ccdc91a6f27e408c9ec42de5cb80341d40ee3e800b1f9f5",
      "ssl_verify": false
    }
  }
}
```

```
./backend.ai mgr etcd put-json volumes volume.json
```
In mgr dbshell update tables fields.
```
update domains set allowed_vfolder_hosts = '{"local:myceph": ["create-vfolder", "modify-vfolder", "delete-vfolder", "mount-in-session", "upload-file", "download-file", "invite-others", "set-user-specific-permission"]}';

update groups set allowed_vfolder_hosts = '{"local:myceph": ["create-vfolder", "modify-vfolder", "delete-vfolder", "mount-in-session", "upload-file", "download-file", "invite-others", "set-user-specific-permission"]}';

update keypair_resource_policies set allowed_vfolder_hosts = '{"local:myceph": ["create-vfolder", "modify-vfolder", "delete-vfolder", "mount-in-session", "upload-file", "download-file", "invite-others", "set-user-specific-permission"]}';
```

# Mounting Ceph-Fuse
On ceph-client machine it is already mounted on install.
```
sudo ceph-fuse -n client.admin --keyring=/etc/ceph/ceph.client.admin.keyring  -m ceph-server-1 /mnt/vfroot/ceph-fuse/
```

# Setting Quotas setup
Login to admin machine: 
```
vagrant ssh ceph-admin
ceph fs authorize test_fs client.admin / rwp
```

Copy the key to the ceph-client at /etc/ceph/ceph.client.admin.keyring

At the ceph-client: mount the ceps-fuse with admin or created client account. 
```
sudo ceph-fuse -n client.admin --keyring=/etc/ceph/ceph.client.admin.keyring  -m ceph-server-1 /mnt/vfroot/ceph-fuse/
sudo mkdir /mnt/vfroot/ceph-fuse/test/
sudo setfattr -n ceph.quota.max_bytes -v 100000000 /mnt/vfroot/ceph-fuse/test/
getfattr -n ceph.quota.max_bytes /mnt/vfroot/ceph-fuse/test/
```
To replace for created client account use example below. However, client keyring should be generated first at admin server.
```
sudo ceph-fuse -n client.foo --keyring=/etc/ceph/ceph.client.foo.keyring  -m ceph-server-1 /mnt/vfroot/ceph-fuse/
```

# Testing quotas using storage proxy
After setting the volume in etcd and postrges tables the quotas can bet tested usng create vfolder command

```
./backend.ai vfolder create myData5 local:volume1 -q 10m
```

Alternatively, if Ceph cluster is not setup you may still able to test the cephfs code intitialization and create vfolder with quota logic.
By applying changes in storage_proxy.toml file by choosing the selected local volume and changend type from 'vfs' to 'cephfs'.
And then by writting debug log statements in cephfs/__init__.py file intercepting the create vfolder flow and quotas. Also, testing the cephfs initialization for the volume.
