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




Setting Up Single Node All-in-one Deployment
--------------------------------------------


3. Prepare a Python distribution whose version matches with the package requirements. (e.g., Backend.AI 22.03 and 22.09 requires Python 3.10) Either:

   - Use the Linux distribution's official package

   - `Use a standalone static build of Python <https://github.com/indygreg/python-build-standalone/releases>`_


   .. warning::

      You also need to make ``pip`` available to the Python installation with the latest ``wheel`` and ``setuptools`` packages, so that any non-binary extension packages can be compiled and installed on your system.

4. Create separate virtualenvs for each service daemons (manager, agent, storage-proxy, and webserver).

5. Install ``backend.ai-SERVICE`` PyPI packages in the respective virtualenvs, where ``SERVICE`` is one of: ``manager``, ``agent``, ``storage-proxy``, and ``webserver``.

6. Refer `the halfstack docker-compose configuration <https://github.com/lablup/backend.ai/blob/main/docker-compose.halfstack-main.yml>`_ (it's a symbolic link so follow the filename in it): copy it and run ``docker compose up -d`` with it.  Adjust the port numbers and volume paths as needed.

   .. tip::

      For details about configuration in the steps 6 to 10, you can just refer `how our development setup script does. <https://github.com/lablup/backend.ai/blob/main/scripts/install-dev.sh>`_

7. Refer `the configuration examples in our repository <https://github.com/lablup/backend.ai/tree/main/configs>`_: copy them and adjust the values according to the above step.
   Be aware that the hostnames and port numbers used to refer other services.
   You must do configuration for all ``SERVICE`` components.
   Place them in either:

   - The current working directory for each ``SERVICE`` daemon

   - ``~/.config/backend.ai``

   - ``/etc/backend.ai``

   .. tip::

      The files named as ``sample`` contain detailed descriptions for each configuration option.

8. Populate the initial etcd configuration as follows.
   etcd serves as a central shared configuration server for all nodes and provides some distributed synchronization primitives.
   The following procedure configures the Redis address to share with all nodes, our public image registry, and the storage proxy.

   .. code-block:: console

      $ source manager/venv/bin/activate
      $ backend.ai mgr etcd put config/redis/addr "127.0.0.1:REDIS_PORT"
      $ backend.ai mgr etcd put config/docker/registry/cr.backend.ai "https://cr.backend.ai"
      $ backend.ai mgr etcd put config/docker/registry/cr.backend.ai/type "harbor2"
      $ backend.ai mgr etcd put config/docker/registry/cr.backend.ai/project "stable,community"  # add multiarch if you are on arm64 machines

   where ``REDIS_PORT`` is the TCP port number to access the Redis server.

   To enable the image registry so that agents can pull images from it, after installation, log in to the web UI using the superadmin account and enable the registry by navigating the "Administration" (side-bar) |rarr| the "Environments" menu |rarr| the "Registries" view.

   Also, populate the storage-proxy configuration to the etcd by copying `configs/manager/sample.etcd.volumes.json <https://github.com/lablup/backend.ai/blob/main/configs/manager/sample.etcd.volumes.json>`_ to ``./volumes.json`` and adjust the settings as you need.
   Note that you must change the secret to a unique random string for secure communication between the manager and storage-proxy.

   .. code-block:: console

      $ source manager/venv/bin/activate
      $ backend.ai mgr etcd put-json volumes ./volumes.json

   To enable access to the volumes defined by the storage-proxy from the users, you need to update the ``allowed_vfolder_hosts`` column of the ``domains`` table to hold the storage volume reference (e.g., "local:volume1").
   You can do this by issuing SQL statement directly inside the PostgreSQL container: ``docker exec -it {PGSQL_CONTAINER_ID} psql postgres://postgres:{DBPASSWORD}@localhost:5432/backend database -c '...';``

   .. note::

      When you install Backend.AI using packages, note that the entry command is changed to ``backend.ai`` instead of ``./backend.ai`` in a development setup using Pants.

9. Populate the database schema and initial fixtures.
   Copy the example JSON files (`fixtures/manager/example-keypairs.json <https://github.com/lablup/backend.ai/blob/main/fixtures/manager/example-keypairs.json>`_, `fixtures/manager/example-resource-presets.json <https://github.com/lablup/backend.ai/blob/main/fixtures/manager/example-resource-presets.json>`_) as ``keypairs.json`` and ``resource-presets.json``.
   Customize them to have unique keypairs and passwords for your initial superadmin and sample user accounts.

   .. code-block:: console

      $ source manager/venv/bin/activate
      $ backend.ai mgr schema oneshot
      $ backend.ai mgr fixture populate ./keypairs.json
      $ backend.ai mgr fixture populate ./resource-presets.json

10. Scan the image registry to fetch the image catalog and metadata.

    .. code-block:: console

       $ source manager/venv/bin/activate
       $ backend.ai mgr image rescan cr.backend.ai

11. Activate each virtualenv and start the services using ``python -m ai.backend.SERVICE.server`` commands, where ``SERVICE`` is one of: ``manager``, ``agent``, ``storage``, and ``web``.

12. If it works, daemonize the service daemons using systemctl or any other desired service supervisor.

    Refer the following systemd configuration sample for an agent.
    As Backend.AI service daemons do not background by themselves, the main process should be kept track of.

    .. code-block:: dosini

       [Unit]
       Description=Backend.AI Agent
       After=network.target remote-fs.target
       Requires=docker.service

       [Service]
       Type=simple
       ExecStart=/home/devops/bin/run-agent.sh
       PIDFile=/home/devops/agent/agent.pid
       WorkingDirectory=/home/devops/agent
       TimeoutStopSec=5
       KillMode=process
       KillSignal=SIGTERM
       PrivateTmp=false
       Restart=on-failure
       RestartSec=10
       LimitNOFILE=5242880
       LimitNPROC=131072

    To activate the virtualenv when run via systemd, write ``run-SERVICE.sh`` files like:

    .. code-block:: shell

       #! /bin/bash
       if [ -z "$HOME" ]; then
         export HOME="/home/devops"
       fi
       # -- If you have installed using pyenv --
       if [ -z "$PYENV_ROOT" ]; then
         export PYENV_ROOT="$HOME/.pyenv"
         export PATH="$PYENV_ROOT/bin:$PATH"
       fi
       eval "$(pyenv init --path)"
       eval "$(pyenv virtualenv-init -)"
       pyenv activate venv-SERVICE  # adjust to your venv names
       # -- (end of pyenv) --
       # -- If you have installed using standard venv --
       source SERVICE/venv/bin/activate  # adjust to your venv paths
       # -- (end of std-venv) --
       if [ "$#" -eq 0 ]; then
         exec python -m ai.backend.SERVICE.server  # adjust to the pkg name
       else
         exec "$@"
       fi

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
