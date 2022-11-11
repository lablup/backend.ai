Install from Packages
=====================

Setting Up Single Node All-in-one Deployment
--------------------------------------------

1. `Configure sysctl/ulimit parameters as recommended. <https://github.com/lablup/backend.ai/blob/main/src/ai/backend/manager/README.md#kernelsystem-configuration>`_

2. Install Docker and Docker Compose v2.

3. Prepare a Python distribution whose version matches with the package requirements. (e.g,. Backend.AI 22.03 and 22.09 requires Python 3.10) Either:

   - Use the Linux distribution's official package

   - `Use a standalone static build of Python <https://github.com/indygreg/python-build-standalone/releases>`_

   - `Use pyenv to manaully build and select a specific Python version <https://github.com/pyenv/pyenv>`_

   .. warning::

      You also need to make ``pip`` available to the Python installation with the latest ``wheel`` and ``setuptools`` packages, so that any non-binary extension packages can be compiled and installed on your system.

4. Create separate virtualenvs for each service daemons (manager, agent, storage-proxy, and webserver).

5. Install ``backend.ai-SERVICE`` PyPI packages in the respective virtualenvs, where ``SERVICE`` is one of: ``manager``, ``agent``, ``storage-proxy``, and ``webserver``.

6. Refer `the halfstack docker-compose configuration <https://github.com/lablup/backend.ai/blob/main/docker-compose.halfstack-main.yml>`_ (it's a symbolic link so follow the filename in it): copy it and run ``docker compose up -d`` with it.  Adjust the port numbers and volume paths as needed.

7. Refer `the configuration examples in our repository <https://github.com/lablup/backend.ai/tree/main/configs>`_: copy them and adjust the values according to the above step. Place them in either:

   - The current working directory for each service daemon

   - ``~/.config/backend.ai``

   - ``/etc/backend.ai``

   .. tip::

      The files named as ``sample`` contain detailed descriptions for each configuration option.

8. Activate each virtualenv and start the service using ``python -m ai.backend.SERVICE.server`` commands, where ``SERVICE`` is one of: ``manager``, ``agent``, ``storage``, and ``web``.

9. If it works, daemonize the service daemons using systemctl or any other desired service supervisor.

Setting Up Accelerators
-----------------------

Ensure that your accelerator is properly set up using vendor-specific installation methods.

Within the virtualenv for ``backend.ai-agent``, additionally install accelerator plugin packages such as ``backend.ai-accelerator-cuda-open``.  Restart the agent.

You also need to configure ``agent.toml``'s ``[agent].allow-compute-plugins`` with the full package path (e.g., ``ai.backend.accelerator.cuda_open``) to activate them.

Setting Up Multiple Nodes Cluster
---------------------------------

Please refer :ref:`multi-node-setup`.

The only difference is that you won't need to configure Pants, but just follow the above instructions to set up Python virtualenvs and install the agent packages for each agent node.

Setting Up Shared Storage
-------------------------

To make vfolders working properly with multiple nodes, you must enable and configure Linux NFS to share a specific directory of the manager node or make a dedicated storage node exposing its volume via NFS (recommended).  You must mount it in the same path in all manager and agent nodes.

It is recommended to unify the UID and GID of the storage-proxy service, all of the agent services across nodes, container UID and GID (configurable in ``agent.toml``), and the NFS volume.
