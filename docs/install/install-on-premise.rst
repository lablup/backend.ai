Install on Premise
==================

The minimal server node configuration:

* 1x SSL certificate with a private key for your own domain (for production)
* 1x manager server
* Nx agent servers
* 1x PostgreSQL server
* 1x Redis server
* 1x etcd cluster

  - For HA setup, it should consist of 5 separate server nodes.

* 1x network-accessible storage server (NAS) with NFS/SMB mounts

  * All should be in the same private network (LAN).

* Depending on the cluster size, several service/database daemons may run on the same physical server.
