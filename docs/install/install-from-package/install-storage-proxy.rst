Install Backend.AI Storage Proxy
================================

Refer to :ref:`prepare_python_and_venv` to setup Python and virtual environment
for the service.

Install the latest version of Backend.AI Storage Proxy for the current Python
version:

.. code-block:: console

   $ cd "${HOME}/storage-proxy"
   $ # Activate a virtual environment if needed.
   $ pip install -U backend.ai-storage-proxy

If you want to install a specific version:

.. code-block:: console

   $ pip install -U backend.ai-storage-proxy==${BACKEND_PKG_VERSION}


Local configuration
-------------------

Backend.AI Storage Proxy uses a TOML file (``storage-proxy.toml``) to configure
local service. Refer to the
`storage-proxy.toml sample file <https://github.com/lablup/backend.ai/blob/main/configs/storage-proxy/sample.toml>`_
for a detailed description of each section and item. A configuration example
would be:

.. code-block:: toml

   [etcd]
   namespace = "local"
   addr = { host = "bai-m1", port = 8120 }
   user = ""
   password = ""

   [storage-proxy]
   node-id = "i-bai-m1"
   num-proc = 2
   pid-file = "/home/bai/storage-proxy/storage_proxy.pid"
   event-loop = "uvloop"
   scandir-limit = 1000
   max-upload-size = "100g"

   # Used to generate JWT tokens for download/upload sessions
   secret = "secure-token-for-users-download-upload-sessions"
   # The download/upload session tokens are valid for:
   session-expire = "1d"

   user = 1100
   group = 1100

   [api.client]
   # Client-facing API
   service-addr = { host = "0.0.0.0", port = 6021 }
   ssl-enabled = false

   [api.manager]
   # Manager-facing API
   service-addr = { host = "0.0.0.0", port = 6022 }
   ssl-enabled = false

   # Used to authenticate managers
   secret = "secure-token-to-authenticate-manager-request"

   [debug]
   enabled = false
   asyncio = false
   enhanced-aiomonitor-task-info = true

   [logging]
   # One of: "NOTSET", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"
   # Set the global logging level.
   level = "INFO"

   # Multi-choice of: "console", "logstash", "file"
   # For each choice, there must be a "logging.<driver>" section
   # in this config file as exemplified below.
   drivers = ["console", "file"]

   [logging.pkg-ns]
   "" = "WARNING"
   "aiotools" = "INFO"
   "aiohttp" = "INFO"
   "ai.backend" = "INFO"

   [logging.console]
   # If set true, use ANSI colors if the console is a terminal.
   # If set false, always disable the colored output in console logs.
   colored = true

   # One of: "simple", "verbose"
   format = "simple"

   [logging.file]
   path = "./logs"
   filename = "storage-proxy.log"
   backup-count = 10
   rotation-size = "10M"

   [volume]

   [volume.local]
   backend = "vfs"
   path = "/vfroot/local"

   # If there are NFS volumes
   # [volume.nfs]
   # backend = "vfs"
   # path = "/vfroot/nfs"

Save the contents to ``${HOME}/.config/backend.ai/storage-proxy.toml``. Backend.AI
will automatically recognize the location. Adjust each field to conform to your
system.


Run Backend.AI Storage Proxy service
------------------------------------

You can run the service:

.. code-block:: console

   $ cd "${HOME}/storage-proxy"
   $ python -m ai.backend.storage.server

Press ``Ctrl-C`` to stop both services.


Register systemd service
------------------------

The service can be registered as a systemd daemon. It is recommended to
automatically run the service after rebooting the host machine, although this is
entirely optional.

First, create a runner script at ``${HOME}/bin/run-storage-proxy.sh``:

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
      exec python -m ai.backend.storage.server
   else
      exec "$@"
   fi

Make the scripts executable:

.. code-block:: console

   $ chmod +x "${HOME}/bin/run-storage-proxy.sh"

Then, create a systemd service file at
``/etc/systemd/system/backendai-storage-proxy.service``:

.. code-block:: dosini

   [Unit]
   Description= Backend.AI Storage Proxy
   Requires=network.target
   After=network.target remote-fs.target

   [Service]
   Type=simple
   ExecStart=/home/bai/bin/run-storage-proxy.sh
   PIDFile=/home/bai/storage-proxy/storage-proxy.pid
   WorkingDirectory=/home/bai/storage-proxy
   User=1100
   Group=1100
   TimeoutStopSec=5
   KillMode=process
   KillSignal=SIGTERM
   PrivateTmp=false
   Restart=on-failure
   RestartSec=10
   LimitNOFILE=5242880
   LimitNPROC=131072

   [Install]
   WantedBy=multi-user.target

Finally, enable and start the service:

.. code-block:: console

   $ sudo systemctl daemon-reload
   $ sudo systemctl enable --now backendai-storage-proxy

   $ # To check the service status
   $ sudo systemctl status backendai-storage-proxy
   $ # To restart the service
   $ sudo systemctl restart backendai-storage-proxy
   $ # To stop the service
   $ sudo systemctl stop backendai-storage-proxy
   $ # To check the service log and follow
   $ sudo journalctl --output cat -u backendai-storage-proxy -f
