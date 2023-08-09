.. role:: raw-html-m2r(raw)
   :format: html

Configuration
-------------

Databases
^^^^^^^^^
:raw-html-m2r:`<span style="background-color:#ffbbb1;border:1px solid #ccc;display:inline-block;width:16px;height:16px;margin:0;padding:0;"></span>`

Redis and PostgreSQL are used to keep track of liveness of agents and compute sessions (which may be composed of one or more kernels).
They also store user metadata such as keypairs and resource usage statistics.

Configuration Management
^^^^^^^^^^^^^^^^^^^^^^^^
:raw-html-m2r:`<span style="background-color:#d1bcd2;border:1px solid #ccc;display:inline-block;width:16px;height:16px;margin:0;padding:0;"></span>`

Most cluster-level configurations are stored in an etcd server or cluster.
The etcd server is also used for service discovery; when new agents boot up they register themselves to the cluster manager via etcd.
For production deployments, we recommend to use an etcd cluster composed of odd (3 or higher) number of nodes to keep high availability.


