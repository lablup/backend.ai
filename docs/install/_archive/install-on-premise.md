# Install on Premise

1. Prepare the instances and databases.
   - 1x SSL certificate with a private key for your own domain (for production)
   - 1x gateway server
   - 1x agent server
   - 1x PostgreSQL server
   - 1x Redis server
   - 1x etcd cluster
     - It is up to you whether to setup a HA-enabled multi-server cluster or a single-server cluster with backups.
     - Check out [[this page|Install etcd]] for details. If you install etcd on the same instance where the manager runs, you could try using docker-compose configuration in this meta-repository's code.
   - 1x network-accessible storage server (NAS) with NFS/SMB mounts
     - All should be in the same private network (LAN).
   - Depending on the cluster size, different service daemons may run on the same physical server.
1. [Install Manager](install/install-manager.md)
1. [Install Agent](install/install-agent.md)
