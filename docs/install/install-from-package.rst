Install from Packages
=====================

.. include:: <isonum.txt>

This guide covers how to install Backend.AI from the official release packages.
You can build a fully-functional Backend.AI cluster with open-source packages.

Backend.AI consists of a
`variety of components <https://github.com/lablup/backend.ai#major-components>`_,
including open-source core components, pluggable extensions, and enterprise
modules. Some of the major components are:

- Backend.AI Manager : API gateway and resource management. Manager delegates
  workload requests to Agent and storage/file requests to Storage Proxy.
- Backend.AI Agent : Installs on a compute node (usually GPU nodes) to start and
  manage the workload execution. It sends periodic heartbeat signals to the
  Manager in order to register itself as a worker node. Even if the connection
  to the Manager is temporarily lost, the pre-initiated workloads continue to
  be executed.
- Backend.AI Storage Proxy : Handles requests relating to storage and files. It
  offloads the Manager's burden of handling long-running file I/O operations. It
  embeds a plugin backend structure that provides dedicated features for each
  storage type.
- Backend.AI Webserver : A web server that provides persistent user web
  sessions. Users can use the Backend.AI features without subsequent
  authentication upon initial login. It also serves the statically built
  graphical user interface in an Enterprise environment.
- Backend.AI Web UI : Web application with a graphical user interface. Users
  can enjoy the easy-to-use interface to launch their secure execution
  environment and use apps like Jupyter and Terminal. It can be served as
  statically built JavaScript via Webserver. Or, it also offers desktop
  applications for many operating systems and architectures.

Most components can be installed in a single management node except Agent,
which is usually installed on dedicated computing nodes (often GPU servers).
However, this is not a rule and Agent can also be installed on the management
node.

It is also possible to configure a high-availability (HA) setup with three or
more management nodes, although this is not the focus of this guide.

.. toctree::
   :maxdepth: 1
   :caption: Table of Contents

   install-from-package/os-preparation
   install-from-package/prepare-database
   install-from-package/prepare-cache-service
   install-from-package/prepare-config-service
   install-from-package/install-manager
   install-from-package/install-agent




Setting Up Single Node All-in-one Deployment
--------------------------------------------



Setting Up Multiple Nodes Cluster
---------------------------------

Please refer :ref:`multi-node-setup`.

The only difference is that you won't need to configure Pants, but just follow the above instructions to set up Python virtualenvs and install the agent packages for each agent node.

Setting Up Shared Storage
-------------------------

To make vfolders working properly with multiple nodes, you must enable and configure Linux NFS to share a specific directory of the manager node or make a dedicated storage node exposing its volume via NFS (recommended).  You must mount it in the same path in all manager and agent nodes.

It is recommended to unify the UID and GID of the storage-proxy service, all of the agent services across nodes, container UID and GID (configurable in ``agent.toml``), and the NFS volume.
