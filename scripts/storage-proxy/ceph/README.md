# Readme


# Installation
1. Set up the vagrant environment and the vagrant machine nodes.
 ```
 mkdir vagrant_box/
 cd vagrant_box
 vagrant plugin install vagrant-cachier
 vagrant plugin install vagrant-hostmanager
 ssh-add -K ~/.vagrant.d/insecure_private_key
 vagrant up
```
2. Log in to the ceph-admin node and run the ceph deployment script.

```
vagrant ssh ceph-admin
sh /vagrant/install_ceph.sh
exit
```

3. Log in to the ceph-client node and install ceph-fuse and the Storage Proxy.
The Storage Proxy is installed in the root `/vagrant` directory, which the host machine shares.
The ceph-fuse mount path is `/mnt/vfroot/ceph-fuse`.
Create the `storage-proxy.toml` config file in the `vagrant_box/` directory.
The `storage-proxy.toml` file contains the updated path.
```
[volume.myceph]
backend="cephfs"
path="/mnt/vfroot/ceph-fuse"
```
Set the etcd IP address to the correct value for the host machine.

Then run ceph-fuse and install the Storage Proxy script on the ceph-client node.

```
vagrant ssh ceph-client
sh /vagrant/install_storage_proxy.sh
```

4. Manager settings
In `volume.json`, set the vagrant network IP address of the ceph-client node if needed.
Add the ceph volume configurations as in the example below.
```
[volume.myceph]
# An extended version for CephFS, which supports extended inode attributes
# for per-directory quota and fast metadata queries.
backend = "cephfs"
path = "/mnt/vfroot/ceph-fuse"
```

An example `volume.json` is:
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
In the manager dbshell, update the table fields.
```
update domains set allowed_vfolder_hosts = '{"local:myceph": ["create-vfolder", "modify-vfolder", "delete-vfolder", "mount-in-session", "upload-file", "download-file", "invite-others", "set-user-specific-permission"]}';

update groups set allowed_vfolder_hosts = '{"local:myceph": ["create-vfolder", "modify-vfolder", "delete-vfolder", "mount-in-session", "upload-file", "download-file", "invite-others", "set-user-specific-permission"]}';

update keypair_resource_policies set allowed_vfolder_hosts = '{"local:myceph": ["create-vfolder", "modify-vfolder", "delete-vfolder", "mount-in-session", "upload-file", "download-file", "invite-others", "set-user-specific-permission"]}';
```

# Mounting Ceph-Fuse
The install step already mounts it on the ceph-client machine.
```
sudo ceph-fuse -n client.admin --keyring=/etc/ceph/ceph.client.admin.keyring  -m ceph-server-1 /mnt/vfroot/ceph-fuse/
```

# Setting quotas
Log in to the admin machine: 
```
vagrant ssh ceph-admin
ceph fs authorize test_fs client.admin / rwp
```

Copy the key to the ceph-client at `/etc/ceph/ceph.client.admin.keyring`.

On the ceph-client, mount the ceph-fuse with the admin account or the created client account.
```
sudo ceph-fuse -n client.admin --keyring=/etc/ceph/ceph.client.admin.keyring  -m ceph-server-1 /mnt/vfroot/ceph-fuse/
sudo mkdir /mnt/vfroot/ceph-fuse/test/
sudo setfattr -n ceph.quota.max_bytes -v 100000000 /mnt/vfroot/ceph-fuse/test/
getfattr -n ceph.quota.max_bytes /mnt/vfroot/ceph-fuse/test/
```
To use the created client account instead, use the example below. Generate the client keyring on the admin server first.
```
sudo ceph-fuse -n client.foo --keyring=/etc/ceph/ceph.client.foo.keyring  -m ceph-server-1 /mnt/vfroot/ceph-fuse/
```

# Testing quotas using the Storage Proxy
After setting the volume in etcd and the PostgreSQL tables, test the quotas with the create vfolder command.

```
./backend.ai vfolder create myData5 local:volume1 -q 10m
```

Alternatively, when no Ceph cluster is set up, you can still test the cephfs code initialization and the vfolder creation with quota logic.
Apply changes in the `storage_proxy.toml` file by selecting the local volume and changing its type from 'vfs' to 'cephfs'.
Then write debug log statements in the `cephfs/__init__.py` file to intercept the vfolder creation and quota flow. Also test the cephfs initialization for the volume.
