Install on Clouds
=================

The minimal instance configuration:

* 1x SSL certificate with a private key for your own domain (for production)
* 1x manager instance (e.g., t3.xlarge on AWS)

  - For HA setup, you many replicate multiple manager instances running in different availability zones and put a load balancer in front of them.

* Nx agent instances (e.g., t3.medium / p2.xlarge on AWS -- for minimal testing)

  - If you spawn multiple agents, it is recommended to use a placement group to improve locality for each availability zone.

* 1x PostgreSQL instance (e.g., AWS RDS)
* 1x Redis instance (e.g., AWS ElasticCache)
* 1x etcd cluster

  - For HA setup, it should consist of 5 separate instances distributed across availability zones.

* 1x cloud file system (e.g., AWS EFS, Azure FileShare)
* All should be in the same virtual private network (e.g., AWS VPC).
