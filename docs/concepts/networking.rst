.. role:: raw-html-m2r(raw)
   :format: html

.. _concept-cluster-networking:
Cluster Networking
------------------

Single-node cluster session
^^^^^^^^^^^^^^^^^^^^^^^^^^^

If a session is created with multiple containers with a single-node option, all containers are created in a single agent.
The containers share a private bridge network in addition to the default network, so that they could interact with each other privately.
There are no firewall restrictions in this private bridge network.

Multi-node cluster session
^^^^^^^^^^^^^^^^^^^^^^^^^^

For even larger-scale computation, you may create a multi-node cluster session that spans across multiple agents.
In this case, the manager auto-configures a private overlay network, so that the containers could interact with each other.
There are no firewall restrictions in this private overlay network.

Detection of clustered setups
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

There is a concept called *cluster role*.
The current version of Backend.AI creates homogeneous cluster sessions by replicating the same resource configuration and the same container image,
but we have plans to add heterogeneous cluster sessions that have different resource and image configurations for each cluster role.
For instance, a Hadoop cluster may have two types of containers: name nodes and data nodes, where they could be mapped to ``main`` and ``sub`` cluster roles.

All interactive apps are executed only in the ``main1`` container which is always present in both cluster and non-cluster sessions.
It is the user application's responsibility to connect with and utilize other containers in a cluster session.
To ease the process, Backend.AI injects the following environment variables into the containers and sets up a random-generated SSH keypairs between the containers so that each container ssh into others without additional prompts.:

.. list-table::
   :header-rows: 1

   * - Environment Variable
     - Meaning
     - Examples
   * - ``BACKENDAI_CLUSTER_SIZE``
     - The number of containers in this cluster session.
     - ``4``
   * - ``BACKENDAI_CLUSTER_HOSTS``
     - A comma-separated list of container hostnames in this cluster session.
     - ``main1,sub1,sub2,sub3``
   * - ``BACKENDAI_CLUSTER_REPLICAS``
     - A comma-separated key:value pairs of cluster roles and the replica counts for each role.
     - ``main:1,sub:3``
   * - ``BACKENDAI_CLUSTER_HOST``
     - The container hostname of the current container.
     - ``main1``
   * - ``BACKENDAI_CLUSTER_IDX``
     - The one-based index of the current container from the containers sharing the same cluster role.
     - ``1``
   * - ``BACKENDAI_CLUSTER_ROLE``
     - The name of the current container's cluster role.
     - ``main``
   * - ``BACKENDAI_CLUSTER_LOCAL_RANK``
     - The zero-based global index of the current container within the entire cluster session.
     - ``0``
