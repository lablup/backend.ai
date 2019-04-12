.. role:: raw-html-m2r(raw)
   :format: html


Key Concepts
------------

Here we describe what the core components of Backend.AI do and why/how we use 3rd-party components.

.. _server-arch-diagram:
.. figure:: server-architecture.svg

   The diagram of a typical multi-node Backend.AI server architecture

The above diagram shows a brief Backend.AI server-side architecture where the components are what you need to install and configure.

Each border-connected group of components is intended to be run on the same server, but you may split them into multiple servers or merge different groups into a single server as you need.
For example, you can run separate servers for the nginx reverse-proxy and the Backend.AI manager or run both on a single server.
In the [[development setup]], all these components run on a single PC such as your laptop.

Kernels
^^^^^^^
:raw-html-m2r:`<span style="background-color:#c1e4f7;border:1px solid #ccc;display:inline-block;width:16px;height:16px;margin:0;padding:0;"></span>`
:raw-html-m2r:`<span style="background-color:#e5f5ff;border:1px solid #ccc;display:inline-block;width:16px;height:16px;margin:0;padding:0;"></span>`

In Backend.AI, we generally call the containers spawned upon user requests as kernels.
In detail, what the user requests is a compute session (with user-provided options), and kernels are the members of that session.
This means that a single compute session may have multiple kernels across different agent servers for parallel and distribute processing.

Note that all kernel images must be downloaded during Backend.AI installation.
Each agent may have different sets of kernel images: for instance, you could set up a cluster where GPU servers have GPU-enabled kernels only while CPU-only servers have other generic programming language kernels.

Manager and Agents
^^^^^^^^^^^^^^^^^^
:raw-html-m2r:`<span style="background-color:#fafafa;border:1px solid #ccc;display:inline-block;width:16px;height:16px;margin:0;padding:0;"></span>`

Backend.AI manager is the central governor of the cluster.
It accepts user requests, creates/destroys the kernels, and routes code execution requests to appropriate agents and kernels.
It also collects the output of kernels and responds the users with them.

Backend.AI agent is a small daemon installed onto individual worker servers to control them.
It manages and monitors the lifecycle of kernel containers, and also mediates the input/output of kernels.
Each agent also reports the resource capacity and status of its server, so that the manager can assign new kernels on idle servers to load balance.

Cluster Networking
^^^^^^^^^^^^^^^^^^
:raw-html-m2r:`<span style="background-color:#99d5ca;border:1px solid #ccc;display:inline-block;width:16px;height:16px;margin:0;padding:0;"></span>`
:raw-html-m2r:`<span style="background-color:#202020;border:1px solid #ccc;display:inline-block;width:16px;height:16px;margin:0;padding:0;"></span>`

You may use your own on-premise server farm or a public cloud service such as AWS, GCP, or Azure.
The primary requirements are:


* The manager server (the HTTPS 443 port) should be exposed to the public Internet or the network that your client can access.
* The manager, agents, and all other database/storage servers should reside at the same local private network where any traffic between them are transparently allowed.
* For high-volume big-data processing, you may want to separate the network for the storage using a secondary network interface on each server.

Databases
^^^^^^^^^
:raw-html-m2r:`<span style="background-color:#ffbbb1;border:1px solid #ccc;display:inline-block;width:16px;height:16px;margin:0;padding:0;"></span>`

Redis and PostgreSQL are used to keep track of liveness of agents and compute sessions (which may be composed of one or more kernels).
They also store user metadata such as keypairs and resource usage statistics.
You can just follow standard installation procedures for them.
To spin up your Backend.AI cluster for the first time, you need to load the SQL schema into the PostgreSQL server, but nothing is required for the Redis server.
Please check out the installation guides for details.

etcd
^^^^
:raw-html-m2r:`<span style="background-color:#d1bcd2;border:1px solid #ccc;display:inline-block;width:16px;height:16px;margin:0;padding:0;"></span>`

etcd is used to share configurations across all the manager and agent servers.
To spin up your Backend.AI cluster for the first time, you need to preload some data into the etcd.
Please check out the installation guides for details.

Virtual Folders
^^^^^^^^^^^^^^^
:raw-html-m2r:`<span style="background-color:#ffdba9;border:1px solid #ccc;display:inline-block;width:16px;height:16px;margin:0;padding:0;"></span>`

Backend.AI abstracts network storages as "virtual folder", which provides a cloud-like private file storage for individual users.
The users may create their own (one or more) virtual folders to store data files, libraries, and program codes.
Virtual folders are mounted into compute session containers at ``/home/work/{name}`` so that user programs have access to the virtual folder contents like a local directory.
As of Backend.AI v18.12, users may also share their own virtual folders with other users with differentiated permissions such as read-only and read-write.

A Backend.AI cluster setup may use any filesystem that provides a local mount point at each node (including the manager and agents) given that the filesystem contents are synchronized across all nodes.
The only requirement is that the local mount-point must be same across all cluster nodes (e.g., ``/mnt/vfroot/mynfs``).
Common setups may use a centralized network storage (served via NFS or SMB), but for more scalability, one might want to use distributed file systems such as CephFS and GlusterFS, or Alluxio that provides fast in-memory cache while backed by another storage server/service such as AWS S3.

For a single-node setup, you may simply use a local empty directory.
