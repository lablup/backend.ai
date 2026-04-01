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

Distributed Training Environment Variables
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

For cluster sessions with more than one container, the following environment variables are
automatically derived from the ``BACKENDAI_*`` cluster variables at container startup to
support distributed training with PyTorch and TensorFlow.

These variables are **not set** for single-container sessions. If a user or image bootstrap
script sets any of these variables before the entrypoint runs, the user-provided value takes
precedence (i.e., no override).

.. note::

   ``WORLD_SIZE``, ``RANK``, and ``LOCAL_RANK`` are intentionally **not** pre-set.
   Launchers like ``torchrun`` set these per-process based on the number of GPUs per node.
   Pre-setting them at the container level would conflict with multi-GPU-per-node setups.

.. list-table::
   :header-rows: 1

   * - Environment Variable
     - Meaning
     - Examples
   * - ``MASTER_ADDR``
     - Hostname of the main container coordinating the cluster session. Derived from the first entry in ``BACKENDAI_CLUSTER_HOSTS``.
     - ``main1``
   * - ``MASTER_PORT``
     - Port number used for distributed communication. Defaults to ``29500`` (PyTorch convention). Override with ``BACKENDAI_DIST_MASTER_PORT``.
     - ``29500``
   * - ``TF_CONFIG``
     - JSON-formatted TensorFlow cluster configuration for this container. Each worker gets a unique port (base port + rank) to avoid conflicts on shared hosts.
     - ``{"cluster": {"worker": ["main1:29500", "sub1:29501"]}, "task": {"type": "worker", "index": 0}}``


Network Security and Isolation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. warning::

   **Critical Security Requirement**
   
   Backend.AI assumes compute nodes (where Agents run) are deployed in a
   network-isolated environment with restricted inbound access from untrusted
   networks. This is a fundamental security requirement for production deployments.

Interactive sessions (notebooks, terminals, web applications) are accessed through
the AppProxy component, which acts as a secure proxy between users and compute sessions.
Direct access to compute nodes must be prevented through proper network configuration.

**Expected Traffic Flow:**

* ✓ User → Webserver → Manager → Agent (session management)
* ✓ User → AppProxy → Agent → Container (interactive sessions)
* ✗ User → Agent (direct access - **MUST BE BLOCKED**)
* ✗ User → Container (direct access - **MUST BE BLOCKED**)

**Key Security Measures:**

1. Deploy agents in a private network with no public IP addresses
2. Configure firewalls to block direct inbound access to compute nodes
3. Only expose necessary services (webserver) to the Internet
4. Use network segmentation between management and compute zones
5. Implement proper firewall rules as documented in the security guide

For detailed network security requirements, architecture diagrams, and configuration
checklists, see :ref:`concept-security`.

.. seealso::

   :ref:`concept-security`

   :doc:`../install/install-from-package/install-agent`
