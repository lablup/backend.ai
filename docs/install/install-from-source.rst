Install from Source
===================

.. note::

   For production deployments, we recommend to create separate virtualenvs for individual services
   and install the pre-built wheel distributions, following :doc:`/install/install-from-package`.


Setting Up Manager and Agent (single node, all-in-one)
------------------------------------------------------

Check out :doc:`/dev/development-setup`.

.. _multi-node-setup:

Setting Up Additional Agents (multi-node)
-----------------------------------------

Updating manager configuration for multi-nodes
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Since ``scripts/install-dev.sh`` assumes a single-node all-in-one setup, it configures the etcd and Redis addresses to be ``127.0.0.1``.

You need to update the etcd configuration of the Redis address so that additional agent nodes can connect to the Redis server using the address advertised via etcd:

.. code-block:: console

   $ ./backend.ai mgr etcd get config/redis/addr
   127.0.0.1:xxxx
   $ ./backend.ai mgr etcd put config/redis/addr MANAGER_IP:xxxx  # use the port number read above

where ``MANAGER_IP`` is an IP address of the manager node accessible from other agent nodes.

Installing additional agents in different nodes
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

First, you need to initialize a working copy of the core repository for each additional agent node.
As our ``scripts/install-dev.sh`` does not yet provide an "agent-only" installation mode,
you need to manually perform the same repository cloning along with the pyenv, Python, and Pants setup procedures as the script does.

.. note::

   Since we use the mono-repo for the core packages, there is no way to separately clone the agent sources only.
   Just clone the entire repository and configure/execute the agent only.
   Ensure that you **also pull the LFS files** when you manually clone it.

Once your ``pants`` is up and working, run ``pants export`` to populate virtualenvs and install dependencies.

Then start to configure ``agent.toml`` by copying it from `configs/agent/halfstack.toml <https://github.com/lablup/backend.ai/blob/main/configs/agent/halfstack.toml>`_ as follows:

* **agent.toml**

  - ``[etcd].addr.host``: Replace with ``MANAGER_IP``

  - ``[agent].rpc-listen-addr.host``: Replace with ``AGENT_IP``

  - ``[container].bind-host``: Replace with ``AGENT_IP``

  - ``[watcher].service-addr.host``: Replace with ``AGENT_IP``

where ``AGENT_IP`` is an IP address of this agent node accessible from the manager and ``MANAGER_IP`` is an IP address of the manager node accessible from this agent node.

Now execute ``./backend.ai ag start-server`` to connect this agent node to an existing manager.

We assume that the agent and manager nodes reside in a same local network, where all TCP ports are open to each other.
If this is not the case, you should configure firewalls to open all the port numbers appearing in ``agent.toml``.

There are more complicated setup scenarios such as splitting network planes for control and container-to-container communications,
but we provide assistance with them for enterprise customers only.

Setting Up Accelerators
-----------------------

Ensure that your accelerator is properly set up using vendor-specific installation methods.

Clone the accelerator plugin package into ``plugins`` directory if necessary or just use one of the already existing one in the mono-repo.

You also need to configure ``agent.toml``'s ``[agent].allow-compute-plugins`` with the full package path (e.g., ``ai.backend.accelerator.cuda_open``) to activate them.

Setting Up Shared Storage
-------------------------

To make vfolders working properly with multiple nodes, you must enable and configure Linux NFS to share the manager node's ``vfroot/local`` directory under the working copy and mount it in the same path in all agent nodes.

It is recommended to unify the UID and GID of the storage-proxy service, all of the agent services across nodes, container UID and GID (configurable in ``agent.toml``), and the NFS volume.

Configuring Overlay Networks for Multi-node Training (Optional)
---------------------------------------------------------------

.. note::

   All other features of Backend.AI except multi-node training work without this configuration.
   The Docker Swarm mode is used to configure overlay networks to ensure privacy between cluster sessions,
   while the container monitoring and configuration is done by Backend.AI itself.

Currently the cross-node inter-container overlay routing is controlled via Docker Swarm's overlay networks.
In the manager, you need to `create a Swarm <https://docs.docker.com/engine/swarm/swarm-tutorial/create-swarm/>`_.
In the agent nodes, you need to `join the Swarm <https://docs.docker.com/engine/swarm/swarm-tutorial/add-nodes/>`_.
Then restart all manager and agent daemons to make it working.
