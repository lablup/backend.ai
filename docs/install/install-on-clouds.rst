
Install on Clouds
-----------------


#. Prepare the instances and databases.


   * 1x SSL certificate with a private key for your own domain (for production)
   * 1x gateway instance (e.g., t2.xlarge on AWS)
   * 1x agent instances (e.g., t2.medium / p2.xlarge on AWS -- for minimal testing)
   * 1x PostgreSQL instance (e.g., AWS RDS)
   * 1x Redis instance (e.g., AWS ElasticCache)
   * 1x etcd cluster

     * It is up to you whether to setup a HA-enabled multi-instance cluster or a single-instance cluster with storage backups.
     * Check out [[this page|Install etcd]] for details. If you install etcd on the same instance where the manager runs, you could try using docker-compose configuration in this meta-repository's code.

   * 1x cloud file system (e.g., AWS EFS, Azure FileShare)
   * All should be in the same virtual private network.

#. :doc:`Install Manager </install/install-manager>`

   * After done, create an image of this instance as a backup.

#. :doc:`Install Agent </install/install-agent>`


   * After done, create an image of this instance for ease of manual/autoamtic scaling.

#. :doc:`Configure Autoscaling </install/configure-autoscaling>`
