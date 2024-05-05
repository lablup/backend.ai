Install Backend.AI Agent
==========================

If there are dedicated compute nodes (often, GPU nodes) in your cluster,
Backend.AI Agent service should be installed on the compute nodes, not on the
management node.

Refer to :ref:`prepare_python_and_venv` to setup Python and virtual environment
for the service.

Install the latest version of Backend.AI Agent for the current Python version:

.. code-block:: console

   $ cd "${HOME}/agent"
   $ # Activate a virtual environment if needed.
   $ pip install -U backend.ai-agent

If you want to install a specific version:

.. code-block:: console

   $ pip install -U backend.ai-agent==${BACKEND_PKG_VERSION}


Setting Up Accelerators
-----------------------

.. note:: You can skip this section if your system does not have H/W accelerators.

Backend.AI supports various H/W accelerators. To integrate them with Backend.AI,
you need to install the corresponding accelerator plugin package. Before
installing the package, make sure that the accelerator is properly set up using
vendor-specific installation methods.

Most popular accelerator today would be NVIDIA GPU. To install the open-source
CUDA accelerator plugin, run:

.. code-block:: console

   $ pip install -U backend.ai-accelerator-cuda-open

.. note::

   Backend.AI's fractional GPU sharing is available only on the enterprise
   version but not supported on the open-source version.


Local configuration
-------------------

Backend.AI Agent uses a TOML file (``agent.toml``) to configure local
service. Refer to the
`agent.toml sample file <https://github.com/lablup/backend.ai/blob/main/configs/agent/sample.toml>`_
for a detailed description of each section and item. A configuration example
would be:

.. code-block:: toml

   [etcd]
   namespace = "local"
   addr = { host = "bai-m1", port = 8120 }
   user = ""
   password = ""

   [agent]
   mode = "docker"
   # NOTE: You cannot use network alias here. Write the actual IP address.
   rpc-listen-addr = { host = "10.20.30.10", port = 6001 }
   # id = "i-something-special"
   scaling-group = "default"
   pid-file = "/home/bai/agent/agent.pid"
   event-loop = "uvloop"
   # allow-compute-plugins = ["ai.backend.accelerator.cuda_open"]

   [container]
   port-range = [30000, 31000]
   kernel-uid = 1100
   kernel-gid = 1100
   bind-host = "bai-m1"
   advertised-host = "bai-m1"
   stats-type = "docker"
   sandbox-type = "docker"
   jail-args = []
   scratch-type = "hostdir"
   scratch-root = "./scratches"
   scratch-size = "1G"

   [watcher]
   service-addr = { host = "bai-a01", port = 6009 }
   ssl-enabled = false
   target-service = "backendai-agent.service"
   soft-reset-available = false

   [logging]
   level = "INFO"
   drivers = ["console", "file"]

   [logging.console]
   colored = true
   format = "verbose"

   [logging.file]
   path = "./logs"
   filename = "agent.log"
   backup-count = 10
   rotation-size = "10M"

   [logging.pkg-ns]
   "" = "WARNING"
   "aiodocker" = "INFO"
   "aiotools" = "INFO"
   "aiohttp" = "INFO"
   "ai.backend" = "INFO"

   [resource]
   reserved-cpu = 1
   reserved-mem = "1G"
   reserved-disk = "8G"

   [debug]
   enabled = false
   skip-container-deletion = false
   asyncio = false
   enhanced-aiomonitor-task-info = true
   log-events = false
   log-kernel-config = false
   log-alloc-map = false
   log-stats = false
   log-heartbeats = false
   log-docker-events = false

   [debug.coredump]
   enabled = false
   path = "./coredumps"
   backup-count = 10
   size-limit = "64M"

You may need to configure ``[agent].allow-compute-plugins`` with the full
package path (e.g., ``ai.backend.accelerator.cuda_open``) to activate them.

Save the contents to ``${HOME}/.config/backend.ai/agent.toml``. Backend.AI
will automatically recognize the location. Adjust each field to conform to your
system.


Run Backend.AI Agent service
----------------------------

You can run the service:

.. code-block:: console

   $ cd "${HOME}/agent"
   $ python -m ai.backend.agent.server

You should see a log message like ``started handling RPC requests at ...``

There is an add-on service, Agent Watcher, that can be used to monitor and manage
the Agent service. It is not required to run the Agent service, but it is
recommended to use it for production environments.

.. code-block:: console

   $ cd "${HOME}/agent"
   $ python -m ai.backend.agent.watcher

Press ``Ctrl-C`` to stop both services.


Register systemd service
------------------------

The service can be registered as a systemd daemon. It is recommended to
automatically run the service after rebooting the host machine, although this is
entirely optional.

It is better to set ``[container].stats-type = "cgroup"`` in the ``agent.toml``
for better metric collection which is only available with root privileges.

First, create a runner script at ``${HOME}/bin/run-agent.sh``:

.. code-block:: bash

   #! /bin/bash
   set -e

   if [ -z "$HOME" ]; then
      export HOME="/home/bai"
   fi

   # -- If you have installed using static python --
   source .venv/bin/activate

   # -- If you have installed using pyenv --
   if [ -z "$PYENV_ROOT" ]; then
      export PYENV_ROOT="$HOME/.pyenv"
      export PATH="$PYENV_ROOT/bin:$PATH"
   fi
   eval "$(pyenv init --path)"
   eval "$(pyenv virtualenv-init -)"

   if [ "$#" -eq 0 ]; then
      exec python -m ai.backend.agent.server
   else
      exec "$@"
   fi

Create a runner script for Watcher at ``${HOME}/bin/run-watcher.sh``:

.. code-block:: bash

   #! /bin/bash
   set -e

   if [ -z "$HOME" ]; then
      export HOME="/home/bai"
   fi

   # -- If you have installed using pyenv --
   if [ -z "$PYENV_ROOT" ]; then
      export PYENV_ROOT="$HOME/.pyenv"
      export PATH="$PYENV_ROOT/bin:$PATH"
   fi
   eval "$(pyenv init --path)"
   eval "$(pyenv virtualenv-init -)"

   if [ "$#" -eq 0 ]; then
      exec python -m ai.backend.agent.watcher
   else
      exec "$@"
   fi

Make the scripts executable:

.. code-block:: console

   $ chmod +x "${HOME}/bin/run-agent.sh"
   $ chmod +x "${HOME}/bin/run-watcher.sh"

Then, create a systemd service file at
``/etc/systemd/system/backendai-agent.service``:

.. code-block:: dosini

   [Unit]
   Description= Backend.AI Agent
   Requires=backendai-watcher.service
   After=network.target remote-fs.target backendai-watcher.service

   [Service]
   Type=simple
   ExecStart=/home/bai/bin/run-agent.sh
   PIDFile=/home/bai/agent/agent.pid
   WorkingDirectory=/home/bai/agent
   TimeoutStopSec=5
   KillMode=process
   KillSignal=SIGINT
   PrivateTmp=false
   Restart=on-failure
   RestartSec=10
   LimitNOFILE=5242880
   LimitNPROC=131072

   [Install]
   WantedBy=multi-user.target

And for Watcher at ``/etc/systemd/system/backendai-watcher.service``:

.. code-block:: dosini

   [Unit]
   Description= Backend.AI Agent Watcher
   After=network.target remote-fs.target

   [Service]
   Type=simple
   ExecStart=/home/bai/bin/run-watcher.sh
   WorkingDirectory=/home/bai/agent
   TimeoutStopSec=3
   KillMode=process
   KillSignal=SIGTERM
   PrivateTmp=false
   Restart=on-failure
   RestartSec=5

   [Install]
   WantedBy=multi-user.target

Finally, enable and start the service:

.. code-block:: console

   $ sudo systemctl daemon-reload
   $ sudo systemctl enable --now backendai-watcher
   $ sudo systemctl enable --now backendai-agent

   $ # To check the service status
   $ sudo systemctl status backendai-agent
   $ # To restart the service
   $ sudo systemctl restart backendai-agent
   $ # To stop the service
   $ sudo systemctl stop backendai-agent
   $ # To check the service log and follow
   $ sudo journalctl --output cat -u backendai-agent -f
