.. role:: raw-html-m2r(raw)
   :format: html


Server Concepts
---------------

Here we describe what the core components of Backend.AI do and why/how we use 3rd-party components.

:raw-html-m2r:`<img src="https://raw.githubusercontent.com/wiki/lablup/backend.ai/images/server-architecture.svg?sanitize=true" alt="Server architecture diagram">`

The above diagram shows a brief Backend.AI server-side architecture where the components are what you need to install and configure.

Each border-connected group of components is intended to be run on the same server, but you may split them into multiple servers or merge different groups into a single server as you need.
For example, you can run separate servers for the nginx reverse-proxy and the Backend.AI manager or run both on a single server.
In the [[development setup]], all these components run on a single PC such as your laptop.

Kernels 
^^^^^^^
.. image:: https://placehold.it/15/c1e4f7/000000?text=+
   :target: https://placehold.it/15/c1e4f7/000000?text=+
   :alt: #c1e4f7
 
.. image:: https://placehold.it/15/e5f5ff/000000?text=+
   :target: https://placehold.it/15/e5f5ff/000000?text=+
   :alt: #e5f5ff

In Backend.AI, we generally call the containers spawned upon user requests as kernels.
In detail, what the user requests is a compute session (with user-provided options), and kernels are the members of that session.
This means that a single compute session may have multiple kernels across different agent servers for parallel and distribute processing.

Note that all kernel images must be downloaded during Backend.AI installation.
Each agent may have different sets of kernel images: for instance, you could set up a cluster where GPU servers have GPU-enabled kernels only while CPU-only servers have other generic programming language kernels.

Manager and Agents 
^^^^^^^^^^^^^^^^^^

.. image:: https://placehold.it/15/fafafa/000000?text=+
   :target: https://placehold.it/15/fafafa/000000?text=+
   :alt: #fafafa

Backend.AI manager is the central governor of the cluster.
It accepts user requests, creates/destroys the kernels, and routes code execution requests to appropriate agents and kernels.
It also collects the output of kernels and responds the users with them.

Backend.AI agent is a small daemon installed onto individual worker servers to control them.
It manages and monitors the lifecycle of kernel containers, and also mediates the input/output of kernels.
Each agent also reports the resource capacity and status of its server, so that the manager can assign new kernels on idle servers to load balance.

Cluster Networking 
^^^^^^^^^^^^^^^^^^
.. image:: https://placehold.it/15/99d5ca/000000?text=+
   :target: https://placehold.it/15/99d5ca/000000?text=+
   :alt: #99d5ca
 
.. image:: https://placehold.it/15/202020/000000?text=+
   :target: https://placehold.it/15/202020/000000?text=+
   :alt: #202020

You may use your own on-premise server farm or a public cloud service such as AWS, GCP, or Azure.
The primary requirements are:


* The manager server (the HTTPS 443 port) should be exposed to the public Internet or the network that your client can access.
* The manager, agents, and all other database/storage servers should reside at the same local private network where any traffic between them are transparently allowed.
* For high-volume big-data processing, you may want to separate the network for the storage using a secondary network interface on each server.

Databases 
^^^^^^^^^
.. image:: https://placehold.it/15/ffbbb1/000000?text=+
   :target: https://placehold.it/15/ffbbb1/000000?text=+
   :alt: #ffbbb1

Redis and PostgreSQL are used to keep track of liveness of agents and compute sessions (which may be composed of one or more kernels).
They also store user metadata such as keypairs and resource usage statistics.
You can just follow standard installation procedures for them.
To spin up your Backend.AI cluster for the first time, you need to load the SQL schema into the PostgreSQL server, but nothing is required for the Redis server.
Please check out the installation guides for details.

etcd 
^^^^
.. image:: https://placehold.it/15/d1bcd2/000000?text=+
   :target: https://placehold.it/15/d1bcd2/000000?text=+
   :alt: #d1bcd2

etcd is used to share configurations across all the manager and agent servers.
To spin up your Backend.AI cluster for the first time, you need to preload some data into the etcd.
Please check out the installation guides for details.

Network Storage 
^^^^^^^^^^^^^^^
.. image:: https://placehold.it/15/ffdba9/000000?text=+
   :target: https://placehold.it/15/ffdba9/000000?text=+
   :alt: #ffdba9

The network storage is used for providing "virtual folder" functions.
The client users may create their own virtual folders to copy data files and shared library files, and then mount the virtual folder when spawning a new compute session to access them like local files.

The implementation can be anything that provides a local mount point at each server including both the manager and agents—Backend.AI only requires a known local UNIX path as configuration that must be same across all manager and agnet servers.
Common setups may use a dedicated NFS or SMB server, but for more scalability, one might want to use distributed file systems such as GlusterFS or Alluxio where their local agents run on each Backend.AI agent servers providing fast in-memory cache while backed by another storage server/service such as AWS S3.

For local development setup, you may simply use a local empty directory for this.
